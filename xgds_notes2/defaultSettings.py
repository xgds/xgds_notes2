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

XGDS_NOTES_MONIKER = 'Notes' # Sometimes we call them Console Log
XGDS_NOTES_ALLOW_MAPPING = True
XGDS_NOTES_ENABLE_GEOCAM_TRACK_MAPPING = True

XGDS_NOTES_NOTE_MODEL = 'xgds_notes2.LocatedNote'
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

# All timestamps in xgds_notes data tables should always use the UTC
# time zone.  XGDS_NOTES_OPS_TIME_ZONE is currently used only to
# choose how to split up days in the daily notes index. We split at
# midnight in the specified time zone. Since ops are usually idle at
# night and we want to split during the idle period, we usually set this
# to the time zone where most ops actually occur.
# note this duplicates functionality in GEOCAM_TRACK so in your siteSettings you might set
# XGDS_NOTES_OPS_TIME_ZONE = GEOCAM_TRACK_OPS_TIME_ZONE
XGDS_NOTES_OPS_TIME_ZONE = 'UTC'

XGDS_NOTES_KML_EXPORT = False

XGDS_NOTES_NOTES_CHANNEL = 'live/notes'

XGDS_NOTES_TAG_TREE_URL = '/notes/tagsTree/'

# These are the columns that will show by default for all note tables.
XGDS_NOTES_TABLE_DEFAULT_COLUMNS = ['event_time', 'zone', 'author', 'content', 'tags', 'link']

BOWER_INSTALLED_APPS = getOrCreateArray('BOWER_INSTALLED_APPS')
BOWER_INSTALLED_APPS += ['moment',
                         'fancytree=fancytree#master',
                         'jquery-ui-contextmenu=https://github.com/mar10/jquery-ui-contextmenu.git',
#                          'bootstrap-tagsinput',
                         'bootstrap-tagsinput=https://github.com/xgds/bootstrap-tagsinput.git#master',
                         'typeahead.js',
                         'datatables-sorting-datetime-moment=https://cdn.datatables.net/plug-ins/1.10.11/sorting/datetime-moment.js'
                         ]

XGDS_MAP_SERVER_JS_MAP = getOrCreateDict('XGDS_MAP_SERVER_JS_MAP')
XGDS_MAP_SERVER_JS_MAP['Note'] = {'ol': 'xgds_notes2/js/olNoteMap.js',
                                      'model': XGDS_NOTES_NOTE_MODEL,
                                      'hiddenColumns': []}

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

#TODO override this to expose the sse channels for notes
XGDS_SSE_NOTE_CHANNELS = []
XGDS_NOTES_CURRENT_MAPPED_FUNCTION = 'xgds_notes.views.defaultCurrentMapNotes'
