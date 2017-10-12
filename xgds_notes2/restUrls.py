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

from django.conf.urls import url
from django.conf import settings

import xgds_notes2.views as views


urlpatterns = [
    url(r'time.txt', views.serverTime, {}, 'server_time'),
    url(r'^tagsTree/?$', views.tagsGetOneLevelTreeJson, {}, 'xgds_notes_get_root_tags'),
    url(r'^tagsTree/(?P<root>[\d]+)$', views.tagsGetOneLevelTreeJson, {}, 'xgds_notes_get_tags'),
    url(r'^tagsChildrenTree/(?P<root>[\d]+)$', views.tagsGetTreeJson, {}, 'xgds_notes_get_tags'),
    url(r'^tagsArray.json$', views.tagsJsonArray, {}, 'xgds_notes_tags_array'),
    url(r'^notes/(?P<app_label>[\w]+)/(?P<model_type>[\w]+)/(?P<obj_pk>[\d]+)$', views.getObjectNotes, {}, 'xgds_notes_object_notes'),

#     url(r'^mapJson/(?P<extens>([\-]*[\d]+\.[\d]+[\,]*)+)$', views.note_json_extens, {'readOnly': True, 'securityTags': ['readOnly']}, 'note_json_extens'),
    ]

if settings.XGDS_NOTES_ENABLE_GEOCAM_TRACK_MAPPING:
    urlpatterns += [url(r'notes.kml', views.note_map_kml, {'readOnly': True, 'securityTags': ['readOnly']}, 'note_map_kml')]
    urlpatterns += [url(r'notesFeed.kml', views.getKmlNetworkLink, {'readOnly': True, 'securityTags': ['readOnly']}, 'note_map_kml_feed')]


