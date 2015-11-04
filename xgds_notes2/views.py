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
from django.http import HttpResponse

from django.shortcuts import render_to_response, redirect, render
from django.http import HttpResponseRedirect, HttpResponseForbidden, Http404
from django.template import RequestContext
from django.utils.translation import ugettext, ugettext_lazy as _

from geocamUtil.datetimeJsonEncoder import DatetimeJsonEncoder
from geocamUtil.loader import LazyGetModelByName

from xgds_notes2.forms import NoteForm, UserSessionForm

if settings.XGDS_SSE:
    from sse_wrapper.events import send_event


Note = LazyGetModelByName(getattr(settings, 'XGDS_NOTES_NOTE_MODEL'))


def server_time(request):
    return HttpResponse(
        datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
        content_type="text"
    )
    
@login_required
def edit_user_session(request):
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
