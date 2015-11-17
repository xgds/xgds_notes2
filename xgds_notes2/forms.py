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

import datetime

from django import forms
from django.conf import settings
from geocamUtil.loader import LazyGetModelByName
from geocamUtil.extFileField import ExtFileField
from geocamUtil.forms.SiteframeChoiceField import SiteframeChoiceField

from xgds_notes2.models import HierarchichalTag
from django.forms.models import ModelChoiceField
from django.forms.fields import ChoiceField

Note = LazyGetModelByName(settings.XGDS_NOTES_NOTE_MODEL)
UserSession = LazyGetModelByName(settings.XGDS_NOTES_USER_SESSION_MODEL)
Tag = LazyGetModelByName(settings.XGDS_NOTES_TAG_MODEL)
Resource = LazyGetModelByName(settings.GEOCAM_TRACK_RESOURCE_MODEL)

class UserSessionForm(forms.ModelForm):
    class Meta:
        model = UserSession.get()
        fields = UserSession.get().getFormFields()


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note.get()
        fields = Note.get().getFormFields()

    date_formats = list(forms.DateTimeField.input_formats) + [
        '%Y/%m/%d %H:%M:%S',
        '%Y/%m/%d %H:%M:%S UTC',
    ]
    event_time = forms.DateTimeField(input_formats=date_formats, required=False)
    extras = forms.CharField(widget=forms.HiddenInput(), required=False)

    # populate the event time with NOW if it is blank.
    def clean_event_time(self):
        etime = self.cleaned_data['event_time']
        if not etime:
            rightnow = datetime.datetime.utcnow()
            return rightnow
        return etime

    def __unicode__(self):
        return self.as_fieldsets()


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag.get()
        fields = Tag.get().getFormFields()

class ImportNotesForm(forms.Form):
    timezone = SiteframeChoiceField(required=True, choices=(('utc', 'UTC'),))
    resource = ModelChoiceField(required=False, queryset=Resource.get().objects.all(), label=settings.GEOCAM_TRACK_RESOURCE_VERBOSE_NAME)
    sourceFile = ExtFileField(ext_whitelist=(".csv", ), required=True)

