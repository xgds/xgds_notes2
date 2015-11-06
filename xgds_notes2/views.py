# __BEGIN_LICENSE__
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
# __END_LICENSE__

from datetime import datetime, timedelta
import itertools
import json

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.http import HttpResponse

from django.shortcuts import render_to_response, redirect, render
from django.http import HttpResponseRedirect, HttpResponseForbidden, Http404
from django.template import RequestContext
from django.utils.translation import ugettext, ugettext_lazy as _

from geocamUtil.datetimeJsonEncoder import DatetimeJsonEncoder
from geocamUtil.loader import LazyGetModelByName, getClassByName
from treebeard.mp_tree import MP_Node

from xgds_notes2.forms import NoteForm, UserSessionForm, TagForm

if settings.XGDS_SSE:
    from sse_wrapper.events import send_event


Note = LazyGetModelByName(getattr(settings, 'XGDS_NOTES_NOTE_MODEL'))
Tag = LazyGetModelByName(getattr(settings, 'XGDS_NOTES_TAG_MODEL'))


def serverTime(request):
    return HttpResponse(
        datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
        content_type="text"
    )
    
@login_required
def editUserSession(request):
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
            return redirect('xgds_notes_record')
        else:
            return HttpResponse("Form Error")
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
        return render(
            request,
            'xgds_notes2/user_session.html',
            {
                'form': form
            },
        )


@login_required
def record(request):
    if request.method == 'POST':

        form = NoteForm(request.POST)
        if form.is_valid():
#             note = form.save(commit=False)
            data = form.cleaned_data

            last_note_values = {}
            request.session['last_note_values'] = last_note_values

            # Hijack the UserSessionForm's validation method to translate enumerations to objects in session data
            session_form = UserSessionForm()
            session_data = {k: session_form.fields[k].clean(v)
                            for k, v in request.session['notes_user_session'].iteritems()
                            if k in session_form.fields}
            data.update(session_data)

            data['author'] = request.user
            tags = data.pop('tags')
            data = {str(k): v
                    for k, v in data.items()}

            del data['extras']
            NOTE_MODEL = Note.get()
            note = NOTE_MODEL(**data)
            for (key, value) in data.items():
                setattr(note, key, value)
            note.creation_time = datetime.utcnow()
            note.modification_time = datetime.utcnow()

            # this is to handle delay state shifting of event time by default it does not change event time
            note.event_time = note.calculateDelayedEventTime()
            note.save()

            if tags:
                note.tags.set(*tags)

            if settings.XGDS_SSE:
                json_data = json.dumps([note.toMapDict()], cls=DatetimeJsonEncoder)
                channels = note.getChannels()
                for channel in channels:
                    send_event('notes', json_data, channel)

            return redirect('xgds_notes_record')
        else:
            return HttpResponse(str(form.errors), status=400)  # Bad Request
    elif request.method == 'GET':

        if 'notes_user_session' not in request.session:
            return redirect('edit_user_session')
        else:
            form = NoteForm()

            usersession_form = UserSessionForm(request.session.get('notes_user_session', None))
            user_session = {field.name: field.field.clean(field.data)
                            for field in usersession_form}

            #notes_list = [ NoteForm(instance=n) for n in Note.get().objects.with_drafts().filter(author=request.user).order_by('-creation_time') ]
            notes_list = Note.get().objects.filter(author=request.user, creation_time__gte=datetime.utcnow() - timedelta(hours=12)).order_by('-creation_time')
            # filter results to notes CREATED < 12 hours old.
#             notes_list = notes_list.filter(creation_time__gte=datetime.utcnow() - timedelta(hours=12))

            return render(
                request,
                'xgds_notes2/record_notes.html',
                {
                    'user': request.user,
                    'user_session': user_session,
                    'form': form,
                    'notes_list': notes_list,
                    'empty_note_form': NoteForm(),
                },
            )
    else:
        raise Exception("Request method %s not supported." % request.method)


def getSortOrder():
    if settings.XGDS_NOTES_SORT_FUNCTION:
        noteSortFn = getClassByName(settings.XGDS_NOTES_SORT_FUNCTION)
        return noteSortFn()
    else:
        return getattr(settings, 'XGDS_NOTES_REVIEW_DEFAULT_SORT', '-event_time')


@login_required
def review(request, **kwargs):
    notes_list = Note.get().objects.all();
    return render(
           request,
           'xgds_notes2/review_notes.html',
           {
               'user': request.user,
               'notes_list': notes_list
           },
       )   

@login_required
def editTags(request):
    return render(
                request,
                'xgds_notes2/tags_tree.html',
                {'addTagForm': TagForm()},
            )

def buildTagJson(root):
    if root is None:
        return []
    root_json = root.getTreeJson()
#     root_json['expanded'] = True
    
#     if root.numchild:
#         children_json = []
#         for child in root.get_children():
#             children_json.append(child.getTreeJson())
#             root_json['children'] = children_json
    return root_json


@never_cache
def getChildrenJson(request, root=None):
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
def getTagsJson(request, root=None):
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
        keys_json.append(buildTagJson(root))
    
    json_data = json.dumps(keys_json)
    return HttpResponse(content=json_data,
                        content_type="application/json")
    

@never_cache
def deleteTag(request, tag_id):
    found_tag = Tag.get().objects.get(pk=tag_id)
    if found_tag:
        if found_tag.get_descendant_count() > 0:
            # TODO need to check all the descendant tags; right now this is disabled.
            return HttpResponse(json.dumps({'failed': found_tag.name + ' had children; cannot delete.'}), content_type='application/json', status=200)
        elif LazyGetModelByName(settings.XGDS_NOTES_TAGGED_NOTE_MODEL).get().objects.filter(tag=found_tag):
            # cannot delete, this tag is in use
            return HttpResponse(json.dumps({'failed': found_tag.name + ' is in use; cannot delete.'}), content_type='application/json', status=200)
        else:
            found_tag.delete()
            return HttpResponse(json.dumps({'success': 'true'}), content_type='application/json')

@login_required
def addRootTag(request):
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            new_root = Tag.get().add_root(**form.cleaned_data)
            return HttpResponse(json.dumps(new_root.getTreeJson()), content_type='application/json')
        else:
            return HttpResponse(json.dumps({'failed': 'Problem adding root: ' + form.errors}), content_type='application/json', status=200)

@login_required
def makeRootTag(request, tag_id):
    if request.method == 'POST':
        tag = Tag.get().objects.get(pk=tag_id)
        if not tag.is_root():
            tag.move(Tag.get().get_root_nodes()[0], 'sorted-sibling')
            return HttpResponse(json.dumps({'success': 'true'}), content_type='application/json')
        else:
            return HttpResponse(json.dumps({'failed': 'Problem making root'}), content_type='application/json', status=200)

            
@login_required
def addTag(request):
    if request.method == 'POST':
        parent_id = request.POST.get('parent_id')
        parent = Tag.get().objects.get(pk=parent_id)
        form = TagForm(request.POST)
        if form.is_valid():
            new_child = parent.add_child(**form.cleaned_data)
            return HttpResponse(json.dumps(new_child.getTreeJson()), content_type='application/json')
        else:
            return HttpResponse(json.dumps({'failed': 'Problem adding tag: ' + form.errors}), content_type='application/json', status=200)


@login_required
def editTag(request, tag_id):
    if request.method == 'POST':
        tag = Tag.get().objects.get(pk=tag_id)
        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            return HttpResponse(json.dumps(tag.getTreeJson()), content_type='application/json')
        else:
            return HttpResponse(json.dumps({'failed': 'Problem editing tag: ' + form.errors}), content_type='application/json', status=200)


@login_required
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
                return HttpResponse(json.dumps({'failed': 'badness.'}), content_type='application/json', status=200)
            