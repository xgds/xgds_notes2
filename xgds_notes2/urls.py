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

from django.views.generic.base import TemplateView

import xgds_notes2.views as views


urlpatterns = patterns('',
                       url(r'^review/?$', views.review, {}, 'xgds_notes_review'),
                       url(r'^record/?$', views.record, {}, 'xgds_notes_record'),
                       url(r'^recordSimple/?$', views.recordSimple, {}, 'record_simple'),
                       url(r'^record/session/?$', views.editUserSession, {}, 'xgds_notes_edit_user_session'),
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
                       
                       )
