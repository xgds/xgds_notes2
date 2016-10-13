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

import cgi
import datetime
import pytz

from django import forms
from django.conf import settings
from django.utils.functional import lazy
from django.contrib.auth.models import User

from geocamTrack.forms import AbstractImportTrackedForm
from geocamUtil.extFileField import ExtFileField
from geocamUtil.forms.AbstractImportForm import getTimezoneChoices
from geocamUtil.loader import LazyGetModelByName
from taggit.forms import *
from xgds_core.forms import SearchForm
from xgds_notes2.models import Role, Location

Note = LazyGetModelByName(settings.XGDS_NOTES_NOTE_MODEL)
UserSession = LazyGetModelByName(settings.XGDS_NOTES_USER_SESSION_MODEL)
Tag = LazyGetModelByName(settings.XGDS_NOTES_TAG_MODEL)
Resource = LazyGetModelByName(settings.GEOCAM_TRACK_RESOURCE_MODEL)

class UserSessionForm(forms.ModelForm):
    class Meta:
        model = UserSession.get()
        fields = UserSession.get().getFormFields()

class NoteForm(forms.ModelForm):
    tags = TagField(required=False,
                    widget=TagWidget(attrs={'class': 'taginput', 
                                            'data-role':'tagsinput',
                                            'placeholder': 'Choose tags'}))
    
    date_formats = list(forms.DateTimeField.input_formats) + [
        '%Y/%m/%d %H:%M:%S',
        '%Y/%m/%d %H:%M:%S UTC',
        '%Y-%m-%d %H:%M:%S UTC',
        '%Y-%m-%dT%H:%M:%S+00:00',
        '%Y-%m-%dT%H:%M:%S 00:00',
        '%Y-%m-%dT%H:%M:%SZ',
    ]
    event_time = forms.DateTimeField(input_formats=date_formats, required=False)
    event_timezone = forms.CharField(widget=forms.HiddenInput(), required=False)
    extras = forms.CharField(widget=forms.HiddenInput(), required=False)

    # for generic foreign key use
    app_label = forms.CharField(widget=forms.HiddenInput(), required=False)
    model_type = forms.CharField(widget=forms.HiddenInput(), required=False)
    object_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    position_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    # populate the event time with NOW if it is blank.
    def clean_event_time(self):
        etime = self.cleaned_data['event_time']
        if not etime:
            rightnow = datetime.datetime.now(pytz.utc)
            return rightnow
        return etime.replace(tzinfo=pytz.utc)
    
    def clean_content(self):
        text = self.cleaned_data['content']
        return cgi.escape(text)

    def __unicode__(self):
        return self.as_fieldsets()
    
    class Meta:
        model = Note.get()
        fields = Note.get().getFormFields()



class TagForm(forms.ModelForm):
    class Meta:
        model = Tag.get()
        fields = Tag.get().getFormFields()


class ImportNotesForm(AbstractImportTrackedForm):
    sourceFile = ExtFileField(ext_whitelist=(".csv", ), required=True)


class SearchNoteForm(SearchForm):
    hierarchy = forms.BooleanField(required=False, label='Include tag descendants')
    tags = TagField(required=False,
                    widget=TagWidget(attrs={'class': 'taginput', 
                                            'data-role':'tagsinput',
                                            'placeholder': 'Choose tags'}))
    
    date_formats = list(forms.DateTimeField.input_formats) + [
        '%Y/%m/%d %H:%M:%S',
        '%Y/%m/%d %H:%M:%S UTC',
        '%Y-%m-%d %H:%M:%S UTC',
        '%Y-%m-%dT%H:%M:%S+00:00',
        '%Y-%m-%dT%H:%M:%S 00:00',
        '%Y-%m-%dT%H:%M:%SZ',
    ]
    min_event_time = forms.DateTimeField(input_formats=date_formats, required=False, label='Min Time')
    max_event_time = forms.DateTimeField(input_formats=date_formats, required=False, label = 'Max Time')
    
    event_timezone = forms.ChoiceField(required=False, choices=lazy(getTimezoneChoices, list)(empty=True))

    role = forms.ModelChoiceField(required=False, queryset=Role.objects.all())
    location = forms.ModelChoiceField(required=False, queryset=Location.objects.all())
    author = forms.ModelChoiceField(required=False, queryset=User.objects.all())
    
    def clean_event_timezone(self):
        if self.cleaned_data['event_timezone'] == 'utc':
            return 'Etc/UTC'
        else:
            return self.cleaned_data['event_timezone']
        return None

    def clean_content(self):
        text = self.cleaned_data['content']
        return cgi.escape(text)

    def buildQueryForField(self, fieldname, field, value, minimum=False, maximum=False):
        # for hierarchichal search or tags, do custom
        # otherwise fall back to base method
        # if fieldname is content, then call sphinx
        if fieldname == 'tags':
            hierarchy = self.cleaned_data['hierarchy']
            return self.buildQueryForTags(fieldname, value, hierarchy)
        elif fieldname == 'hierarchy':
            return None
        return super(SearchNoteForm, self).buildQueryForField(fieldname, field, value, minimum, maximum)
        

    class Meta:
        model = Note.get()
        fields = Note.get().getSearchFormFields()
