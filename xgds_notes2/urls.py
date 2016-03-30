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

from django.conf.urls import patterns, include, url
from django.conf import settings


import xgds_notes2.views as views


urlpatterns = [
    url(r'^review/?$', views.review, {}, 'xgds_notes_review'),
    url(r'^record/?$', views.record, {}, 'xgds_notes_record'),
    url(r'^recordSimple/?$', views.recordSimple, {}, 'record_simple'),
    url(r'^editNote/(?P<note_pk>[\d]+)$', views.editNote, {}, 'xgds_notes_edit_note'),
    url(r'^editNote/$', views.editNote, {}, 'xgds_notes_edit_note'),
    url(r'^record/session/?$', views.editUserSession, {}, 'xgds_notes_edit_user_session'),
    url(r'^record/session/ajax/?$', views.editUserSession, {'ajax':True}, 'xgds_notes_edit_user_session_ajax'),
    url(r'time.txt', views.serverTime, {}, 'server_time'),
    url(r'^editTags/?$', views.editTags, {}, 'xgds_notes_edit_tags'),
    url(r'^addRootTag/?$', views.addRootTag, {}, 'xgds_notes_add_root_tag'),
    url(r'^addTag/?$', views.addTag, {}, 'xgds_notes_add_tag'),
    url(r'^moveTag/?$', views.moveTag, {}, 'xgds_notes_move_tag'),
    url(r'^makeRoot/(?P<tag_id>[\d]+)$', views.makeRootTag, {}, 'xgds_notes_move_tag'),
    url(r'^editTag/(?P<tag_id>[\d]+)$', views.editTag, {}, 'xgds_notes_edit_tag'),
    url(r'^tagsTree/?$', views.tagsGetOneLevelTreeJson, {}, 'xgds_notes_get_root_tags'),
    url(r'^tagsTree/(?P<root>[\d]+)$', views.tagsGetOneLevelTreeJson, {}, 'xgds_notes_get_tags'),
    url(r'^tagsChildrenTree/(?P<root>[\d]+)$', views.tagsGetTreeJson, {}, 'xgds_notes_get_tags'),
    url(r'^deleteTag/(?P<tag_id>[\d]+)$', views.deleteTag, {}, 'xgds_notes_delete_tag'),
    url(r'^tagsArray.json$', views.tagsJsonArray, {}, 'xgds_notes_tags_array'),
    url(r'^import/?$', views.importNotes, {}, 'xgds_notes_import'),
    url(r'^notes/(?P<app_label>[\w]+)/(?P<model_type>[\w]+)/(?P<obj_pk>[\d]+)$', views.getObjectNotes, {}, 'xgds_notes_object_notes'),
#     url(r'^mapJson/(?P<extens>([\-]*[\d]+\.[\d]+[\,]*)+)$', views.note_json_extens, {'readOnly': True, 'loginRequired': False, 'securityTags': ['readOnly']}, 'note_json_extens'),
    ]

if settings.XGDS_NOTES_ENABLE_GEOCAM_TRACK_MAPPING:
    urlpatterns += [url(r'notes.kml', views.note_map_kml, {'readOnly': True, 'loginRequired': False, 'securityTags': ['readOnly']}, 'note_map_kml')]
    urlpatterns += [url(r'notesFeed.kml', views.getKmlNetworkLink, {'readOnly': True, 'loginRequired': False, 'securityTags': ['readOnly']}, 'note_map_kml_feed')]

if settings.XGDS_SSE:
    from sse_wrapper.views import EventStreamView
    urlpatterns += [
        url(r'^live/notes/(?P<filter>[\w]+:[\w]+)/$', views.getNotesJson, {}, 'xgds_notes_liveNotes'),
        url(r'^live/notes-stream/(?P<channel_extension>[\w]+:[\w]+)/$', EventStreamView.as_view(channel='live/notes'), {}, 'xgds_notes_liveNotes_stream'),

        url(r'^live/notes/$', views.getNotesJson, {}, 'xgds_notes_liveNotes'),
        url(r'^live/notes-stream/$', EventStreamView.as_view(channel='live/notes'), {}, 'xgds_notes_liveNotes_stream'),
        ]

