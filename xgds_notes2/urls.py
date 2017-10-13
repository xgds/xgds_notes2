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

from django.conf.urls import url, include
from django.conf import settings

import xgds_notes2.views as views


urlpatterns = [
    url(r'^record/?$', views.record, {}, 'xgds_notes_record'),
    url(r'^recordSimple/?$', views.recordSimple, {}, 'record_simple'),
    url(r'^editNote/(?P<note_pk>[\d]+)$', views.editNote, {}, 'xgds_notes_edit_note'),
    url(r'^record/session/?$', views.editUserSession, {}, 'xgds_notes_edit_user_session'),
    url(r'^record/session/ajax/?$', views.editUserSession, {'ajax':True}, 'xgds_notes_edit_user_session_ajax'),
    url(r'^editTags/?$', views.editTags, {}, 'xgds_notes_edit_tags'),
    url(r'^addRootTag/?$', views.addRootTag, {}, 'xgds_notes_add_root_tag'),
    url(r'^addTag/?$', views.addTag, {}, 'xgds_notes_add_tag'),
    url(r'^moveTag/?$', views.moveTag, {}, 'xgds_notes_move_tag'),
    url(r'^makeRoot/(?P<tag_id>[\d]+)$', views.makeRootTag, {}, 'xgds_notes_move_tag'),
    url(r'^editTag/(?P<tag_id>[\d]+)$', views.editTag, {}, 'xgds_notes_edit_tag'),
    url(r'^deleteTag/(?P<tag_id>[\d]+)$', views.deleteTag, {}, 'xgds_notes_delete_tag'),
    url(r'^import/?$', views.importNotes, {}, 'xgds_notes_import'),
    url(r'^searchMap$', views.notesSearchMap, {}, 'search_xgds_notes_map'),
    url(r'^searchMap/(?P<filter>(([\w]+|[a-zA-Z0-9:._\-\s]+),*)+)$', views.notesSearchMap, {}, 'search_xgds_notes_map_filter'),

    # Including these in this order ensures that reverse will return the non-rest urls for use in our server
    url(r'^rest/', include('xgds_notes2.restUrls')),
    url('', include('xgds_notes2.restUrls')),

    ]


if False and settings.XGDS_SSE:
    from sse_wrapper.views import EventStreamView
    urlpatterns += [
        url(r'^live/notes/(?P<filter>[\w]+:[\w]+)/$', views.getNotesJson, {}, 'xgds_notes_liveNotes'),
        url(r'^live/notes-stream/(?P<channel_extension>[\w]+:[\w]+)/$', EventStreamView.as_view(channel='live/notes'), {}, 'xgds_notes_liveNotes_stream'),

        url(r'^live/notes/$', views.getNotesJson, {}, 'xgds_notes_liveNotes'),
        url(r'^live/notes-stream/$', EventStreamView.as_view(channel='live/notes'), {}, 'xgds_notes_liveNotes_stream'),
        ]

