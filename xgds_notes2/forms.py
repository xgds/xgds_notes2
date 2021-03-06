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

# from haystack.query import SearchQuerySet
from django import forms
from django.conf import settings
from django.utils.functional import lazy
from django.db.models import Q
from dateutil.parser import parse as dateparser

from dal import autocomplete

from geocamUtil.extFileField import ExtFileField
from geocamUtil.forms.AbstractImportForm import getTimezoneChoices
from geocamUtil.loader import LazyGetModelByName
from taggit.forms import *
from xgds_core.models import XgdsUser
from xgds_core.forms import SearchForm, AbstractImportVehicleForm

from xgds_map_server.models import Place
from xgds_map_server.forms import buildQueryForPlace
from xgds_notes2.models import Role, Location, HierarchichalTag
from xgds_notes2.utils import buildQueryForTags

NOTE_MODEL = LazyGetModelByName(settings.XGDS_NOTES_NOTE_MODEL)
MESSAGE_MODEL = LazyGetModelByName(settings.XGDS_NOTES_MESSAGE_MODEL)
USER_SESSION_MODEL = LazyGetModelByName(settings.XGDS_NOTES_USER_SESSION_MODEL)
TAG_MODEL = LazyGetModelByName(settings.XGDS_NOTES_TAG_MODEL)

PLACE_FILTER_URL = '/xgds_core/complete/%s.json/' % 'xgds_map_server.Place'


class UserSessionForm(forms.ModelForm):
    class Meta:
        model = USER_SESSION_MODEL.get()
        fields = USER_SESSION_MODEL.get().getFormFields()


class NoteForm(forms.ModelForm):
    tags = TagField(required=False,
                    widget=TagWidget(attrs={'class': 'taginput', 
                                            'data-role':'tagsinput',
                                            'placeholder': 'Choose tags'}))

    note_submit_url = forms.CharField(widget=forms.HiddenInput(), initial='/notes/recordSimple/',  required=False)
    
    event_time = forms.DateTimeField(input_formats=settings.XGDS_CORE_DATE_FORMATS, required=False)
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
        model = NOTE_MODEL.get()
        fields = NOTE_MODEL.get().getFormFields()


class TagForm(forms.ModelForm):
    class Meta:
        model = TAG_MODEL.get()
        fields = TAG_MODEL.get().getFormFields()


class ImportNotesForm(AbstractImportVehicleForm):
    sourceFile = ExtFileField(ext_whitelist=(".csv", ), required=True)


class SearchMessageForm(SearchForm):

    min_event_time = forms.DateTimeField(input_formats=settings.XGDS_CORE_DATE_FORMATS, required=False,
                                         label='Min Time',
                                         widget=forms.DateTimeInput(attrs={'class': 'datetimepicker'}))
    max_event_time = forms.DateTimeField(input_formats=settings.XGDS_CORE_DATE_FORMATS, required=False,
                                         label='Max Time',
                                         widget=forms.DateTimeInput(attrs={'class': 'datetimepicker'}))

    event_timezone = forms.ChoiceField(required=False, choices=lazy(getTimezoneChoices, list)(empty=True),
                                       label='Time Zone', help_text='Required for Min/Max Time')

    author = forms.ModelChoiceField(XgdsUser.objects.all(),
                                    required=False,
                                    widget=autocomplete.ModelSelect2(url='select2_model_user'))

    field_order = MESSAGE_MODEL.get().getSearchFieldOrder()

    # populate the times properly
    def clean_min_event_time(self):
        return self.clean_time('min_event_time', self.clean_event_timezone())

    # populate the times properly
    def clean_max_event_time(self):
        return self.clean_time('max_event_time', self.clean_event_timezone())

    def clean_event_timezone(self):
        if self.cleaned_data['event_timezone'] == 'utc':
            return 'Etc/UTC'
        else:
            return self.cleaned_data['event_timezone']
        return None

    def clean_content(self):
        text = self.cleaned_data['content']
        return cgi.escape(text)

    def clean(self):
        cleaned_data = super(SearchMessageForm, self).clean()
        event_timezone = cleaned_data.get("event_timezone")
        min_event_time = cleaned_data.get("min_event_time")
        max_event_time = cleaned_data.get("max_event_time")

        if max_event_time or min_event_time:
            if not event_timezone:
                self.add_error('event_timezone', "Time Zone is required for min / max times.")
                raise forms.ValidationError(
                    "Time Zone is required for min / max times."
                )
            else:
                del cleaned_data["event_timezone"]

    def buildQueryForField(self, fieldname, field, value, minimum=False, maximum=False):
        # TODO if fieldname is content, then call sphinx

        if fieldname == 'content':
            return self.buildContainsQuery(fieldname, field, value)
        return super(SearchMessageForm, self).buildQueryForField(fieldname, field, value, minimum, maximum)

    class Meta:
        model = MESSAGE_MODEL.get()
        fields = MESSAGE_MODEL.get().getSearchFormFields()


class SearchNoteForm(SearchMessageForm):
    hierarchy = forms.BooleanField(required=False, label='Include tag descendants')
    tags = TagField(required=False,
                    widget=TagWidget(attrs={'class': 'taginput', 
                                            'data-role':'tagsinput',
                                            'placeholder': 'Choose tags'}))
    
    role = forms.ModelChoiceField(required=False, queryset=Role.objects.all())
    location = forms.ModelChoiceField(required=False, queryset=Location.objects.all())

    place_hierarchy = forms.BooleanField(required=False, label='Include %s descendants' % settings.XGDS_MAP_SERVER_PLACE_MONIKER)

    place = forms.ModelChoiceField(Place.objects.all(),
                                   label=settings.XGDS_MAP_SERVER_PLACE_MONIKER,
                                   required=False,
                                   widget=autocomplete.ModelSelect2(url=PLACE_FILTER_URL))

    field_order = NOTE_MODEL.get().getSearchFieldOrder()
    
    def buildQueryForField(self, fieldname, field, value, minimum=False, maximum=False):
        # for hierarchichal search or tags, do custom
        # otherwise fall back to base method
        # if fieldname is content, then call sphinx

        if fieldname == 'tags':
            hierarchy = self.cleaned_data['hierarchy']
            return buildQueryForTags(fieldname, field, value, hierarchy)
        if fieldname == 'place':
            place_hierarchy = self.cleaned_data['place_hierarchy']
            return buildQueryForPlace(fieldname, field, value, place_hierarchy)
        elif fieldname == 'hierarchy' or fieldname == 'place_hierarchy':
            return None
        elif fieldname == 'content':
            return self.buildContainsQuery(fieldname, field, value)
        return super(SearchNoteForm, self).buildQueryForField(fieldname, field, value, minimum, maximum)

    class Meta:
        model = NOTE_MODEL.get()
        fields = NOTE_MODEL.get().getSearchFormFields()
