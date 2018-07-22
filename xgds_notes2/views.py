#__BEGIN_LICENSE__
# Copyright (c) 2015, United States Government, as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All rights reserved.
#
# The xGDS platform is licensed under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
#__END_LICENSE__

import traceback
import cgi
import re
from datetime import datetime, timedelta
import itertools
import json
import pytz
import csv
import ast

from dateutil.parser import parse as dateparser

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.views.decorators.cache import never_cache
from django.http import HttpResponse, JsonResponse
from django.core.urlresolvers import reverse

from django.shortcuts import redirect, render
from django.template.loader import render_to_string

from geocamUtil.datetimeJsonEncoder import DatetimeJsonEncoder
from geocamUtil.loader import LazyGetModelByName, getClassByName
from geocamUtil.modelJson import modelToDict
from geocamUtil import TimeUtil

from geocamTrack.utils import getClosestPosition

from treebeard.mp_tree import MP_Node

from xgds_notes2.forms import NoteForm, UserSessionForm, TagForm, ImportNotesForm
from xgds_core.views import getTimeZone, addRelay, getDelay
from xgds_core.flightUtils import getFlight
from xgds_map_server.views import getSearchPage, getSearchForms, buildFilterDict
from models import HierarchichalTag
from httplib2 import ServerNotFoundError
from apps.xgds_notes2.forms import SearchNoteForm

if False and settings.XGDS_SSE:
    from sse_wrapper.events import send_event
    
UNSET_SESSION = 'Unset Session'

Note = LazyGetModelByName(getattr(settings, 'XGDS_NOTES_NOTE_MODEL'))
Tag = LazyGetModelByName(getattr(settings, 'XGDS_NOTES_TAG_MODEL'))


def serverTime(request):
    return HttpResponse(
        datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S'),
        content_type="text"
    )


def editUserSession(request, ajax=False):

    # display a form to edit the content of the UserSession object in request.session['notes_user_session']
    existing_data = request.session.get('notes_user_session', None)
    if request.method == 'POST':
        form = UserSessionForm(request.POST)
        if form.is_valid():
            request.session['notes_user_session'] = form.data.dict()
            #persist the session data in user preferences, if that feature is available (see plrpExplorer.models.UserPreferences)
            if hasattr(request.user, 'preferences'):
                for field in form.fields:
                    request.user.preferences['default_' + field] = form.data[field]
            if not ajax:
                return redirect('search_xgds_notes_map')
            else:
                resultDict = {'success': True}
                for key, value in form.cleaned_data.iteritems():
                    resultDict[key] = str(value);
                return HttpResponse(json.dumps(resultDict),
                                    content_type='application/json')

        else:
            return HttpResponse(json.dumps(form.errors),
                                content_type='application/json',
                                status=406)
    else:
        defaults = {}
        if hasattr(request.user, 'preferences'):
            empty_form = UserSessionForm()  # Used as a source of enum choices
            for fieldname in empty_form.fields:
                if 'default_' + fieldname in itertools.chain(request.user.preferences.keys(), getattr(settings, 'DEFAULT_USER_PREFERENCES', [])):
                    value = request.user.preferences.get('default_' + fieldname)
                    defaults[fieldname] = value
        if existing_data:
            defaults.update(existing_data)  # merge anything in the session store with the user preferences
        form = UserSessionForm(initial=defaults)
        template = 'xgds_notes2/user_session.html'
        return render(
            request,
            template,
            {
                'form': form
            },
        )


def populateNoteData(request, form):
    """ Populate the basic data dictionary for a new note from a submitted form
    Form must already be valid
    """
    errors = []
    data = form.cleaned_data

    # Hijack the UserSessionForm's validation method to translate enumerations to objects in session data
    if 'notes_user_session' in request.session.keys():
        session_form = UserSessionForm()
        session_data = {k: session_form.fields[k].clean(v)
                        for k, v in request.session['notes_user_session'].iteritems()
                        if k in session_form.fields}
        data.update(session_data)
    else:
        errors.append(UNSET_SESSION)

    if request.user:
        data['author'] = request.user
    
    if data['app_label'] and data['model_type']:
        data['content_type'] = ContentType.objects.get(app_label=data['app_label'], model=data['model_type'])
    data.pop('app_label')
    data.pop('model_type')
    tags = data.pop('tags')
    
    # handle extras
    try:
        extras = data.pop('extras')
        if str(extras) != 'undefined':
            extrasDict = ast.literal_eval(extras)
            data.update(extrasDict)
    except:
        pass
    
    # This is for relay purposes
    if 'id' in request.POST:
        data['id'] = request.POST['id']
    
    return data, tags, errors


def linkTags(note, tags):
    if tags:
        note.tags.clear()
        for t in tags:
            try:
                tag = HierarchichalTag.objects.get(pk=int(t))
                note.tags.add(tag)
            except:
                tag = HierarchichalTag.objects.get(slug=t)
                note.tags.add(tag)
        note.save()


def createNoteFromData(data, delay=True, serverNow=False):
    NOTE_MODEL = Note.get()
    empty_keys = [k for k,v in data.iteritems() if v is None]
    for k in empty_keys:
        del data[k]
    try:
        del data['note_submit_url']
    except:
        pass
    note = NOTE_MODEL(**data)
    for (key, value) in data.items():
        setattr(note, key, value)
    note.creation_time = datetime.now(pytz.utc)
    note.modification_time = note.creation_time

    # if we are taking a note on an object, get the flight and position from the object
    if note.content_object:
        try:
            if hasattr(note, 'flight'):
                note.flight = note.content_object.flight
            note.position = note.content_object.getPosition()
        except:
            pass
    else:
        if delay:
            # this is to handle delay state shifting of event time by default it does not change event time
            note.event_time = note.calculateDelayedEventTime(data['event_time'])
        elif serverNow:
            note.event_time = note.calculateDelayedEventTime(note.creation_time)
        if not note.event_timezone:
            note.event_timezone = getTimeZone(note.event_time)

    if hasattr(note, 'flight') and not note.flight:
        # hook up the flight, this should always be true
        note.flight = getFlight(note.event_time)
        # TODO handle using the vehicle that came in from session

    # hook up the position if it can have one
    if hasattr(note, 'position') and not note.position:
        note.lookupPosition()

    note.save()
    return note


def record(request):
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():

            data, tags, errors = getClassByName(settings.XGDS_NOTES_POPULATE_NOTE_DATA)(request, form)

            data = {str(k): v
                    for k, v in data.items()}

            if 'author_id' in request.POST:
                data['author'] = User.objects.get(id=request.POST['author_id'])

            delay = getDelay()
            note = createNoteFromData(data, delay=delay>0)
            linkTags(note, tags)
            jsonNote = json.dumps([note.toMapDict()], cls=DatetimeJsonEncoder)

            # Right now we are using relay for the show on map
            if note.show_on_map:
                if settings.XGDS_CORE_REDIS and settings.XGDS_SSE:
                    note.broadcast()
                mutable = request.POST._mutable
                request.POST._mutable = True
                request.POST['id'] = note.pk
                request.POST['author_id'] = note.author.id
                request.POST._mutable = mutable
                addRelay(note, None, json.dumps(request.POST, cls=DatetimeJsonEncoder), reverse('xgds_notes_record'))

            return HttpResponse(jsonNote,
                                content_type='application/json')
#             if not settings.XGDS_SSE:
#                 return HttpResponse(jsonNote,
#                                     content_type='application/json')
#             else:
#                 return HttpResponse(json.dumps({'success': 'true'}), content_type='application/json')

        else:
            return HttpResponse(str(form.errors), status=400)  # Bad Request
    else:
        raise Exception("Request method %s not supported." % request.method)


def recordSimple(request):
    if request.method != 'POST':
        return HttpResponse(json.dumps({'error': {'code': -32099,
                                                  'message': 'You must post, cheater.'}
                                        }),
                            content_type='application/json')

    form = NoteForm(request.POST)
    if form.is_valid():
        data, tags, errors = getClassByName(settings.XGDS_NOTES_POPULATE_NOTE_DATA)(request, form)
        note = createNoteFromData(data, False, 'serverNow' in request.POST)
        linkTags(note, tags)
        json_data = json.dumps([note.toMapDict()], cls=DatetimeJsonEncoder)

        # Right now we are using relay for the show on map
        if note.show_on_map:
            if settings.XGDS_CORE_REDIS and settings.XGDS_SSE:
                note.broadcast()
            mutable = request.POST._mutable
            request.POST._mutable = True
            request.POST['id'] = note.pk
            request.POST['author_id'] = note.author.id
            request.POST._mutable = mutable
            addRelay(note, None, json.dumps(request.POST, cls=DatetimeJsonEncoder), reverse('xgds_notes_record'))

        return HttpResponse(json_data,
                            content_type='application/json')
    else:
        return JsonResponse({'error': {'code': -32099,
                                       'message': 'problem submitting note',
                                       'data': form.errors}
                                        },
                            safe=False,
                            status=406)


def editNote(request, note_pk=None):
    try:
        tags_list = []
        note = Note.get().objects.get(pk=int(note_pk))
        tags_changed = False
        if len(request.POST) == 1:
            note.tags.clear()
        else:
            for key, value in request.POST.iteritems():
                strkey = str(key)
                if strkey.startswith('data'):
                    p = re.compile(r'^data\[(?P<pk>\d+)\]\[(?P<attr>\w*)\]')
                    m = p.match(strkey)
                    if m:
                        attr = m.group('attr')
                        if attr == 'content':
                            setattr(note, attr, cgi.escape(str(value)))
                        elif attr == 'tag_names':
                            tags_changed = True
                            tag_regex = re.compile(r'^data\[(?P<pk>\d+)\]\[(?P<attr>\w*)\]\[(?P<index>\d+)\]\[(?P<tag_attr>\w*)\]')
                            tag_match = tag_regex.match(strkey)
                            if tag_match:
                                tag_attr = tag_match.group('tag_attr')
                                if tag_attr == 'id':
                                    tags_list.append(int(value))
                        else:
                            setattr(note, attr, str(value))

        note.modification_time = datetime.now(pytz.utc)
        if tags_changed:
            linkTags(note, tags_list)
        else:
            note.save()
        return HttpResponse(json.dumps({'data': [note.toMapDict()]}, cls=DatetimeJsonEncoder),
                            content_type='application/json')
    except:
        traceback.print_exc()
        return HttpResponse(json.dumps({'error': {'code': -32099,
                                                  'message': 'problem submitting note'
                                                  }
                                        }),
                            content_type='application/json')



def getSortOrder():
    if settings.XGDS_NOTES_SORT_FUNCTION:
        noteSortFn = getClassByName(settings.XGDS_NOTES_SORT_FUNCTION)
        return noteSortFn()
    else:
        return getattr(settings, 'XGDS_NOTES_REVIEW_DEFAULT_SORT', '-event_time')


def editTags(request):
    return render(
                request,
                'xgds_notes2/tags_tree.html',
                {'addTagForm': TagForm()},
            )

def tagsGetRootTreesJson(root):
    if root is None:
        return []
    root_json = root.getTreeJson()
    return root_json


def tagsJsonArray(request):
    allTags = Tag.get().objects.all()
    return HttpResponse(json.dumps([tag.toSimpleDict() for tag in allTags], separators=(', ',': ')).replace("},","},\n").replace("}]","}\n]"),
                        content_type="application/json"
    )


def tagsSearchJsonArray(request):
    search_term = request.GET.get('term', '')
    # TODO: execute a prefix search with Sphinx, if available
    tfilter = Tag.get().objects.filter
    result = []
    for tag in tfilter(name__istartswith=search_term):
        result.append(tag.name)
    
    for tag in tfilter(abbreviation__istartswith=search_term):
        result.append(tag.abbreviation)
    result.sort()

    return HttpResponse(json.dumps(result),
                        content_type="application/json"
    )

@never_cache
def tagsGetTreeJson(request, root=None):
    """
    json tree of children
    note that this does json for jstree
    """
    root = Tag.get().objects.get(pk=root)
    children_json = []
    if root.numchild:
        for child in root.get_children():
            children_json.append(child.getTreeJson())
    
    json_data = json.dumps(children_json)
    return HttpResponse(content=json_data,
                        content_type="application/json")

@never_cache
def tagsGetOneLevelTreeJson(request, root=None):
    """
    json tree of tags one level deep
    note that this does json for jstree
    """
    roots = []
    if not root:
        roots = Tag.get().get_root_nodes()
    else:
        roots.append(Tag.get().objects.get(pk=root))
    
    keys_json = []
    for root in roots:
        keys_json.append(tagsGetRootTreesJson(root))
    
    json_data = json.dumps(keys_json)
    return HttpResponse(content=json_data,
                        content_type="application/json")
    

@never_cache
def deleteTag(request, tag_id):
    found_tag = Tag.get().objects.get(pk=tag_id)
    if found_tag:
        if found_tag.numchild > 0:
            # TODO need to check all the descendant tags; right now this is disabled.
            return HttpResponse(json.dumps({'failed': found_tag.name + " has children, cannot delete."}), content_type='application/json', status=406)
        elif LazyGetModelByName(settings.XGDS_NOTES_TAGGED_NOTE_MODEL).get().objects.filter(tag=found_tag):
            # cannot delete, this tag is in use
            return HttpResponse(json.dumps({'failed': found_tag.name + ' is in use; cannot delete.'}), content_type='application/json', status=406)
        else:
            found_tag.delete()
            return HttpResponse(json.dumps({'success': 'true'}), content_type='application/json')

def addRootTag(request):
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            new_root = Tag.get().add_root(**form.cleaned_data)
            return HttpResponse(json.dumps(new_root.getTreeJson()), content_type='application/json')
        else:
            return HttpResponse(json.dumps({'failed': 'Problem adding root: ' + form.errors}), content_type='application/json', status=406)

def makeRootTag(request, tag_id):
    if request.method == 'POST':
        tag = Tag.get().objects.get(pk=tag_id)
        if not tag.is_root():
            tag.move(Tag.get().get_root_nodes()[0], 'sorted-sibling')
            return HttpResponse(json.dumps({'success': 'true'}), content_type='application/json')
        else:
            return HttpResponse(json.dumps({'failed': 'Problem making root'}), content_type='application/json', status=406)

            
def addTag(request):
    if request.method == 'POST':
        parent_id = request.POST.get('parent_id')
        parent = Tag.get().objects.get(pk=parent_id)
        form = TagForm(request.POST)
        if form.is_valid():
            new_child = parent.add_child(**form.cleaned_data)
            return HttpResponse(json.dumps(new_child.getTreeJson()), content_type='application/json')
        else:
            return HttpResponse(json.dumps({'failed': 'Problem adding tag: ' + form.errors}), content_type='application/json', status=406)


def editTag(request, tag_id):
    if request.method == 'POST':
        tag = Tag.get().objects.get(pk=tag_id)
        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            return HttpResponse(json.dumps(tag.getTreeJson()), content_type='application/json')
        else:
            return HttpResponse(json.dumps({'failed': 'Problem editing tag: ' + form.errors}), content_type='application/json', status=406)


def moveTag(request):
    if request.method == 'POST':
        parent_id = request.POST.get('parent_id')
        tag_id = request.POST.get('tag_id')
        found_tag = Tag.get().objects.get(pk=tag_id)
        found_parent = Tag.get().objects.get(pk=parent_id)
        if found_tag and found_parent:
            try:
                found_tag.move(found_parent, 'sorted-child')
                return HttpResponse(json.dumps({'success': 'true'}), content_type='application/json')
            except:
                return HttpResponse(json.dumps({'failed': 'badness.'}), content_type='application/json', status=406)

def doImportNotes(request, sourceFile, tz, vehicle):
    dictreader = csv.DictReader(sourceFile)
    for row in dictreader:
        row['author'] = request.user
        if row['content'] or row['tags']:
            if 'first_name' in row and 'last_name' in row:
                if row['first_name'] and row['last_name']:
                    try:
                        row['author'] = User.objects.get(first_name=row['first_name'], last_name=row['last_name'])
                        del row['first_name']
                        del row['last_name']
                    except:
                        pass
        if row['event_time']:
            event_time = dateparser(row['event_time'])
            if tz != pytz.utc:
                localized_time = tz.localize(event_time)
                event_time = TimeUtil.timeZoneToUtc(localized_time)
            row['event_time'] = event_time 
        
        try:
            # TODO implement tags when ready
            del row['tags']
        except:
            pass
        
        NOTE_MODEL = Note.get()
        note = NOTE_MODEL(**row)
        note.creation_time = datetime.now(pytz.utc)
        note.modification_time = datetime.now(pytz.utc)
        
        if vehicle:
            note.position = getClosestPosition(timestamp=note.event_time, vehicle=vehicle)
        note.save()
    
    
def importNotes(request):
    errors = None
    if request.method == 'POST':
        form = ImportNotesForm(request.POST, request.FILES)
        if form.is_valid():
            doImportNotes(request, request.FILES['sourceFile'], form.getTimezone(), form.getVehicle())
            return redirect('search_xgds_notes_map')
        else:
            errors = form.errors
    return render(
        request,
        'xgds_notes2/import_notes.html',
        {
            'form': ImportNotesForm(),
            'errorstring': errors
        },
    )


def getObjectNotes(request, app_label, model_type, obj_pk):
    """
    For a given object, get the notes on that object and return as a json dictionary from oldest to newest
    """
    ctype = ContentType.objects.get(app_label=app_label, model=model_type)
    result = Note.get().objects.filter(content_type__pk = ctype.id, object_id=obj_pk).order_by('event_time', 'creation_time')
    resultList = []
    for n in result:
        resultList.append(n.toMapDict())
    json_data = json.dumps(resultList, cls=DatetimeJsonEncoder)
    return HttpResponse(content=json_data,
                        content_type="application/json")


def buildNotesForm(args):
    theForm = SearchNoteForm(args)
    return theForm

def notesSearchMap(request, filter=None):
    noteType = Note.get().cls_type()
    return getSearchPage(request, noteType, 'xgds_notes2/map_record_notes.html', True, getSearchForms(noteType, filter))

# @never_cache
# def getNotesJson(request, filter=None, range=0, isLive=1):
#     """ Get the note json information to show in table or map views.
#     """
#     try:
#         isLive = int(isLive)
#         if filter:
#             splits = str(filter).split(":")
#             filterDict = {splits[0]: splits[1]}
# 
#         range = int(range)
#         if isLive or range:
#             if range==0:
#                 range = 6
#             now = datetime.now(pytz.utc)
#             yesterday = now - timedelta(seconds=3600 * range)
#             if not filter:
#                 notes = Note.get().objects.filter(creation_time__lte=now).filter(creation_time__gte=yesterday)
#             else:
#                 allNotes = Note.get().objects.filter(**filterDict)
#                 notes = allNotes.filter(creation_time__lte=now).filter(creation_time__gte=yesterday)
#         elif filter:
#             notes = Note.get().objects.filter(**filterDict)
#         else:
#             notes = Note.get().objects.all()
#     except:
#         return HttpResponse(json.dumps({'error': {'message': 'I think you passed in an invalid filter.',
#                                                   'filter': filter}
#                                         }),
#                             content_type='application/json')
# 
#     if notes:
#         keepers = []
#         for note in notes:
#             resultDict = note.toMapDict()
#             keepers.append(resultDict)
#         json_data = json.dumps(keepers, indent=4, cls=DatetimeJsonEncoder)
#         return HttpResponse(content=json_data,
#                             content_type="application/json")
#     else:
#         return HttpResponse(json.dumps({'error': {'message': 'No notes found.',
#                                                   'filter': filter}
#                                         }),
#                             content_type='application/json')

# @never_cache
# def note_json_extens(request, extens, today=False):
#     """ Get the note json information to show in the fancy tree. this gets all notes in the mapped area
#     """
#     splits = str(extens).split(',')
#     minLon = float(splits[0])
#     minLat = float(splits[1])
#     maxLon = float(splits[2])
#     maxLat = float(splits[3])
# 
#     queryString = Note.get().getMapBoundedQuery(minLon, minLat, maxLon, maxLat)
#     if queryString:
#         found_notes = Note.get().objects.raw(queryString)
#         if found_notes:
#             keepers = []
#             for note in found_notes:
#                 resultDict = note.toMapDict()
#                 keepers.append(resultDict)
#             json_data = json.dumps(keepers, indent=4, cls=DatetimeJsonEncoder)
#             return HttpResponse(content=json_data,
#                                 content_type="application/json")
#         return ""

    
if settings.XGDS_NOTES_ENABLE_GEOCAM_TRACK_MAPPING:
    from geocamUtil.KmlUtil import wrapKmlDjango, djangoResponse

    def getKmlNetworkLink(request):
        ''' This refreshes note_map_kml every 5 seconds'''
        url = request.build_absolute_uri(settings.SCRIPT_NAME + 'notes/rest/notes.kml')
        return djangoResponse('''
    <NetworkLink>
      <name>%(name)s</name>
      <Link>
        <href>%(url)s</href>
        <refreshMode>onInterval</refreshMode>
        <refreshInterval>5</refreshInterval>
      </Link>
    </NetworkLink>
    ''' % dict(name=settings.XGDS_NOTES_MONIKER,
               url=url))

    @never_cache
    def note_map_kml(request, range=12):
        now = datetime.now(pytz.utc)
        yesterday = now - timedelta(seconds=3600 * range)
        objects = Note.get().objects.filter(show_on_map=True).filter(creation_time__lte=now).filter(creation_time__gte=yesterday)
        days = []
        if objects:
            days.append({'date': now,
                        'notes': objects
                        })

        if days:
            kml_document = render_to_string(
                'xgds_notes2/notes_placemark_document.kml',
                {'days': days},
                request
            )
            return wrapKmlDjango(kml_document)
        return wrapKmlDjango("")

def getSseNoteChannels(request):
    # Look up the note channels we are using for SSE
    return JsonResponse(settings.XGDS_SSE_NOTE_CHANNELS, safe=False)


def defaultCurrentMapNotes(request):
    return HttpResponseRedirect(reverse('xgds_map_server_objectsJson', kwargs={'object_name': 'XGDS_NOTES_NOTE_MODEL',
                                                                               'filter':{'show_on_map': True}}))

def getCurrentMapNotes(request):
    getNotesFunction = getClassByName(settings.XGDS_NOTES_CURRENT_MAPPED_FUNCTION)
    return getNotesFunction(request)
