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

from geocamUtil.SettingsUtil import getOrCreateDict, getOrCreateArray

"""
This app may define some new parameters that can be modified in the
Django settings module.  Let's say one such parameter is FOO.  The
default value for FOO is defined in this file, like this:

  FOO = 'my default value'

If the admin for the site doesn't like the default value, they can
override it in the site-level settings module, like this:

  FOO = 'a better value'

Other modules can access the value of FOO like this:

  from django.conf import settings
  print settings.FOO

Don't try to get the value of FOO from django.conf.settings.  That
settings object will not know about the default value!
"""

XGDS_NOTES_MODEL_NAME = 'Note' # used for building filters
XGDS_NOTES_NOTE_MODEL = 'xgds_notes2.LocatedNote'
XGDS_NOTES_NOTE_MONIKER = 'Note'
XGDS_NOTES_MONIKER = XGDS_NOTES_NOTE_MONIKER + 's' # Sometimes we call them Console Log

XGDS_NOTES_MESSAGE_MODEL_NAME = 'Message' # used for building filters
XGDS_NOTES_MESSAGE_MODEL = 'xgds_notes2.LocatedMessage'
XGDS_NOTES_MESSAGE_MONIKER = 'Message'
XGDS_NOTES_MESSAGES_MONIKER = XGDS_NOTES_MESSAGE_MONIKER + 's'

XGDS_NOTES_ALLOW_MAPPING = True
XGDS_NOTES_ENABLE_GEOCAM_TRACK_MAPPING = True

XGDS_NOTES_TAG_MODEL = 'xgds_notes2.HierarchichalTag'
XGDS_NOTES_TAGGED_NOTE_MODEL = 'xgds_notes2.TaggedNote'

XGDS_NOTES_USER_SESSION_MODEL = 'xgds_notes2.UserSession'

XGDS_NOTES_POPULATE_NOTE_DATA = 'xgds_notes2.views.populateNoteData'
XGDS_NOTES_BUILD_NOTES_FORM = 'xgds_notes2.views.buildNotesForm'

XGDS_NOTES_REVIEW_DEFAULT_SORT = '-event_time'

# If the default sort is not adequate, you can define a function to do your sort order for review.
# It currently takes no parameters.
XGDS_NOTES_SORT_FUNCTION = None

# Override this in your application with the path to a django_filters.FilterSet subclass to customise the available filters.
XGDS_NOTES_REVIEW_FILTER_CLASS = None

XGDS_NOTES_KML_EXPORT = False

XGDS_NOTES_NOTES_CHANNEL = 'live/notes'

XGDS_NOTES_TAG_TREE_URL = '/notes/tagsTree/'

STATIC_URL = '/static/'
EXTERNAL_URL = STATIC_URL

XGDS_MAP_SERVER_JS_MAP = getOrCreateDict('XGDS_MAP_SERVER_JS_MAP')
XGDS_MAP_SERVER_JS_MAP[XGDS_NOTES_NOTE_MONIKER] = {'ol': 'xgds_notes2/js/olNoteMap.js',
                                                   'model': XGDS_NOTES_NOTE_MODEL,
                                                   'columns': ['checkbox', 'event_time', 'event_timezone', 'author_name', 'content', 'tag_names','content_url', 'content_thumbnail_url', 'content_name', 'app_label', 'model_type', 'type', 'lat', 'lon', 'alt', 'flight_name','object_type', 'object_id', 'creation_time','show_on_map', 'role_name', 'location_name', 'pk'],
                                                   'hiddenColumns': ['app_label', 'model_type', 'type', 'lat', 'lon', 'alt', 'role_name', 'location_name', 'flight_name', 'content_thumbnail_url', 'content_name', 'object_type', 'object_id', 'creation_time','show_on_map','pk'],
                                                   'searchableColumns': ['name','description','flight_name', 'author_name', 'role_name', 'location_name',],
                                                   'editableColumns':{'content':'text','tag_names':'tagsinput'},
                                                   'unsortableColumns': ['content_url'],
                                                   #[{'label':'Content','name':'content','data':5},
                                                   #                   {'label':'Tags','name':'tag_names','data':6}],
                                                   'columnTitles': ['Time', 'TZ', 'Author', 'Content', 'Tags', 'Link'],
                                                   'viewHandlebars': 'xgds_notes2/templates/handlebars/note-view.handlebars',
                                                   'viewJS': [STATIC_URL + 'xgds_notes2/js/genericNotesView.js' ],
                                                   'viewInitMethods': ['xgds_notes.initDetailView'],
                                                   'searchInitMethods': ['xgds_notes.initializeInput'],
                                                   'event_time_field': 'event_time',
                                                   'event_timezone_field': 'event_timezone',
                                                   'search_form_class': 'xgds_notes2.forms.SearchNoteForm'}


XGDS_MAP_SERVER_JS_MAP[XGDS_NOTES_MESSAGE_MONIKER] = {'ol': 'xgds_notes2/js/olMessageMap.js',
                                                   'model': XGDS_NOTES_MESSAGE_MODEL,
                                                   'columns': ['checkbox', 'event_time', 'event_timezone', 'author_name', 'content', 'lat', 'lon', 'alt', 'flight_name', 'app_label', 'model_type', 'type', 'pk'],
                                                   'hiddenColumns': ['app_label', 'model_type', 'type', 'lat', 'lon', 'alt', 'flight_name', 'pk'],
                                                   'searchableColumns': ['content','flight_name', 'author_name', ],
                                                   'editableColumns':{'content':'text'},
                                                   'columnTitles': ['Time', 'TZ', 'Author', 'Content',],
                                                   'viewHandlebars': 'xgds_notes2/templates/handlebars/message-view.handlebars',
                                                   'event_time_field': 'event_time',
                                                   'event_timezone_field': 'event_timezone',
                                                   'search_form_class': 'xgds_notes2.forms.SearchMessageForm'}

XGDS_DATA_IMPORTS = getOrCreateDict('XGDS_DATA_IMPORTS')
XGDS_DATA_IMPORTS[XGDS_NOTES_MONIKER] = '/notes/import'

XGDS_DATA_MASKED_FIELDS = getOrCreateDict('XGDS_DATA_MASKED_FIELDS')
XGDS_DATA_MASKED_FIELDS['xgds_notes'] = {'Note': ['uuid',
                                                  'draft',
                                                  'event_time',
                                                  'creation_time',
                                                  'modification_time',
                                                  'console_position',
                                                  'tagged_items',
                                                  'asset_position',
                                                  'new_asset_position',
                                                  'still_frame',
                                                  ]
                                        }

# XGDS_DATA_EXPAND_RELATED = getOrCreateDict('XGDS_DATA_EXPAND_RELATED')
# XGDS_DATA_EXPAND_RELATED['xgds_notes'] = {  'Note': [('asset_position', 'depth', 'Depth'),
#                                                      ('new_asset_position', 'depthMeters', 'New Depth'),
#                                                      ('tags', 'all', 'Tags'),
#                                                      ],
#  
#                                             }

# TODO override this to expose the sse channels for notes
# Typically they will be broadcast per vehicle, so for example if you have
# tracked vehicles A and B, it will be ['A','B']

XGDS_SSE_NOTE_CHANNELS = []
XGDS_NOTES_CURRENT_MAPPED_FUNCTION = 'xgds_notes.views.defaultCurrentMapNotes'

XGDS_NOTES_MAP_NOTE_CHANNEL = 'map_note'
XGDS_NOTES_NOTE_CHANNEL = 'note'
XGDS_NOTES_MESSAGE_CHANNEL = 'message'

