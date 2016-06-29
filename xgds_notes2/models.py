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
import traceback
from django.utils import timezone

from django.db import models
from django.db.models.query import QuerySet
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from django.template.loader import get_template
from django.template import Context

from geocamUtil.loader import LazyGetModelByName, getModelByName
from geocamUtil.models import AbstractEnumModel
from geocamUtil.modelJson import modelToDict
from geocamUtil.defaultSettings import HOSTNAME
from geocamUtil.UserUtil import getUserName

from geocamTrack.models import PastResourcePosition
# from geocamTrack.utils import getClosestPosition

from treebeard.mp_tree import MP_Node
from taggit.models import TagBase, ItemBase
from taggit.managers import TaggableManager

from xgds_core.models import SearchableModel


class HierarchichalTag(TagBase, MP_Node):
    node_order_by = ['name']
    abbreviation = models.CharField(max_length=8, blank=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    
    def preSave(self):
        self.name = self.name.lower()
        
    def getTreeJson(self):
        """ get the JSON block for fancytree """
        title = self.name
        if self.abbreviation:
            title = title + '(' + self.abbreviation + ')'
        result = {"title": title,
                  "key": self.pk,
                  "tooltip": self.description,
                  "extraClasses": 'tag',
                  "lazy": True,
                  "data": {"parentId": None,
                           "name": self.name,
                           "abbreviation": self.abbreviation,
                           "description": self.description
                           }
                  }
        parent = self.get_parent()
        if parent:
            result['data']['parentId'] = parent.pk
        return result
    
    @classmethod
    def getFormFields(cls):
        return ["abbreviation", "name", "description"]
    
    def toSimpleDict(self):
        return {'id': self.id,
                'name': self.name,
                'abb': self.abbreviation,
                'slug': self.slug}

DEFAULT_TAGGED_NOTE_FIELD = lambda: models.ForeignKey("LocatedNote", related_name='%(app_label)s_%(class)s_related')

class AbstractTaggedNote(ItemBase):
    content_object = 'set to DEFAULT_TAGGED_NOTE_FIELD() or similar in derived classes'
    tag = models.ForeignKey('xgds_notes2.HierarchichalTag',
                            related_name="%(app_label)s_%(class)s_related",
                            blank=True)


    @classmethod
    def tags_for(cls, model, instance=None, **extra_filters):
        kwargs = extra_filters or {}
        if instance is not None:
            kwargs.update({
                '%s__content_object' % cls.tag_relname(): instance
            })
            return cls.tag_model().objects.filter(**kwargs)
        kwargs.update({
            '%s__content_object__isnull' % cls.tag_relname(): False
        })
        return cls.tag_model().objects.filter(**kwargs).distinct()

    class Meta:
        abstract = True


class TaggedNote(AbstractTaggedNote):
    content_object = DEFAULT_TAGGED_NOTE_FIELD()


class MissionDay(models.Model):
    name = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    def __unicode__(self):
        return unicode(self.name)

    @property
    def range(self):
        return (self.start_time, self.end_time)

    def contains(self, date_time):
        return date_time >= self.start_time and date_time <= self.end_time

    @classmethod
    def for_datetime(cls, date_time):
        qs = cls.objects.filter(start_time__lte=date_time, end_time__gte=date_time)
        if qs.count() == 1:
            return qs[0]
        elif qs.count() == 0:
            return None
        else:
            raise Exception("Found more than one MissionDay for datetime %s" % str(date_time))


class Role(AbstractEnumModel):
    pass


class Location(AbstractEnumModel):
    pass


class AbstractUserSession(models.Model):
    role = models.ForeignKey(Role)

    @classmethod
    def getFormFields(cls):
        return ['role']
    
    class Meta:
        abstract = True
      

class UserSession(AbstractUserSession):
    location = models.ForeignKey(Location)
    
    @classmethod
    def getFormFields(cls):
        return ['role',
                'location']
    

DEFAULT_TAGGABLE_MANAGER = lambda: TaggableManager(through=TaggedNote, blank=True)

class AbstractNote(models.Model, SearchableModel):
    ''' Abstract base class for notes
    '''
#     # custom id field for uniqueness
#     id = models.CharField(max_length=128,
#                           unique=True, blank=False,
#                           editable=False, primary_key=True)

    # Override this to specify a list of related fields
    # to be join-query loaded when notes are listed, as an optimization
    # prefetch for reverse or for many to many.
    prefetch_related_fields = ['tags']

    # select related for forward releationships.  
    select_related_fields = ['author', 'role', 'location']

    show_on_map = models.BooleanField(default=False) # broadcast this note on the map by default

    event_time = models.DateTimeField(null=True, blank=False, db_index=True)
    event_timezone = models.CharField(null=True, blank=False, max_length=128, default=settings.TIME_ZONE, db_index=True)
    creation_time = models.DateTimeField(blank=True, default=timezone.now, editable=False, db_index=True)
    modification_time = models.DateTimeField(blank=True, default=timezone.now, editable=False, db_index=True)

    author = models.ForeignKey(User)
    role = models.ForeignKey(Role, null=True)
    location = models.ForeignKey(Location, null=True)

    content = models.TextField(blank=True, null=True)
    
    tags = "set to DEFAULT_TAGGABLE_MANAGER() or similar in any derived classes"
    
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.CharField(max_length=128, null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    @property
    def object_type(self):
        if self.content_type:
            return self.content_type.model_class().cls_type()
        return None

    @classmethod
    def cls_type(cls):
        return 'Note'

    @property
    def tag_ids(self):
        return None

    @property
    def tag_names(self):
        result = []
        for tag in self.tags.get_query_set():
            result.append(tag.name)
        return result
#             return [t.encode('utf-8') for t in self.tags.names()]
#         return None
    
    @property
    def role_name(self):
        if self.role:
            return self.role.display_name
        return None
    
    @property
    def location_name(self):
        if self.location:
            return self.location.display_name
        return None
    
    @property
    def author_name(self):
        return getUserName(self.author)

    class Meta:
        abstract = True
        ordering = ['event_time']
        permissions = (
            ('edit_all_notes', 'Can edit notes authored by others.'),
        )
        
    def __unicode__(self):
        return "%s: %s" % (self.event_time, self.content)
    
    @classmethod
    def getFormFields(cls):
        return ['event_time',
                'content',
                'tags',
                'show_on_map',
                ]
    
# For sphinx to work right - these next 2 lines *MUST* be in the inherited concrete
# class. Will fail miserably if it tries to search on this abstract class.
#    if "SphinxSearch" in globals():
#        search = SphinxSearch()

    def adjustedEventTime(self):
        """
        This is so derived classes can adapt event time for display
        """
        return self.event_time

    def calculateDelayedEventTime(self):
        """
        This is so derived classes can adapt event time in the case of being in "delay" mode
        """
        return self.event_time

    def to_kml(self, animated=False, timestampLabels=False, ignoreLabels=None):
        "Define me, or override in your subclass"
        raise NotImplementedError

    def getLabel(self):
        """
        Get the KML note label, use tag if exists or content otherwise
        """
        result = ""
#         if self.tags:
#             tags_list = self.tags.all()
#             result = "".join(str(x) + " " for x in tags_list)
        if result == "":
            result = self.content[:12]
        return result

    
    @property
    def content_url(self):
        if self.content_object:
            return self.content_object.view_time_url(self.event_time)
        return None

    @property
    def content_name(self):
        if self.content_object:
            return self.content_object.name
        return None
    
    @property
    def thumbnail_time_url(self, event_time):
        return self.content_thumbnail_url
    
    @property
    def content_thumbnail_url(self):
        if self.content_object:
            return self.content_object.thumbnail_time_url(self.event_time)
        return None

#     def toMapDict(self):
#         """
#         Return a reduced dictionary that will be turned to JSON for rendering in a map
#         """
#         columns = settings.XGDS_MAP_SERVER_JS_MAP[self.cls_type()]['columns']
#         values =  self.toMapList(columns)
#         result = dict(zip(columns, values))
#         return result
#         

    @staticmethod
    def getMapBoundedQuery(minLon, minLat, maxLon, maxLat, today=False):
        """
        Implement this in your note that has a position to return a query that will filter notes by position
        """
        return None

    def getChannels(self):
        """ for sse, return a list of channels """
        return [settings.XGDS_NOTES2_NOTES_CHANNEL]

    @classmethod
    def getSearchableFields(self):
        return ['content', 'author__first_name', 'author__last_name']
    
class Note(AbstractNote):
    '''
    Non-Abstract note class (with no position)
    '''
    tags = DEFAULT_TAGGABLE_MANAGER()


DEFAULT_POSITION_FIELD = lambda: models.ForeignKey(PastResourcePosition, null=True, blank=True)

class AbstractLocatedNote(AbstractNote):
    """ This is a basic note with a location, pulled from the current settings for geocam track past position model.
    """
    position = "set to DEFAULT_POSITION_FIELD() or similar in derived classes"
      
    def to_kml(self, animated=False, timestampLabels=False, ignoreLabels=None):
        if ignoreLabels is None:
            ignoreLabels = []
        # if no label is associated with the note, we'll fall back to a timetamp-based label anyway.
        notelabel = None
        if timestampLabels or (self.label and self.label.value in ignoreLabels):
            atime = self.adjustedEventTime()
            notelabel = "%02d:%02d" % (atime.hour, atime.minute)
        else:
            notelabel = self.getLabel()
  
        if not notelabel:
            atime = self.adjustedEventTime()
            try:
                altitude = self.position.altitude
                notelabel = "%s %02d:%02d" % (altitude, atime.hour, atime.minute)
            except:
                notelabel = "%02d:%02d" % (atime.hour, atime.minute)
  
        return get_template('note.kml').render(Context({
            'note': self,
            'animated': animated,
            'notelabel': notelabel,
        }))
          
#     def toMapDict(self):
#         """
#         Return a reduced dictionary that will be turned to JSON for rendering in a map
#         """
#         result = AbstractNote.toMapDict(self)
#         if result['position']:
#             result['lon'] = self.position.longitude
#             result['lat'] = self.position.latitude
#             try:
#                 result['heading'] = self.position.heading
#             except:
#                 result['heading'] = ''
#             try:
#                 result['altitude'] = self.position.altitude
#             except:
#                 result['altitude'] = ''
#               
#         else:
#             result['lat'] = ''
#             result['lon'] = ''
#             result['heading'] = ''
#             result['altitude'] = ''
#   
#         del(result['position'])
#         return result
      
    @staticmethod
    def getMapBoundedQuery(minLon, minLat, maxLon, maxLat, today=False):
        bounds = {'minLon': minLon,
                  'minLat': minLat,
                  'maxLon': maxLon,
                  'maxLat': maxLat}
        qstring = 'select n.* from %s n, %s a where (n.position_id = a.id) and '
        qstring += '(a.longitude<=%(maxLon).9f and a.longitude>=%(minLon).9f) and '
        qstring += '(a.latitude>=%(minLat).9f and a.latitude<=%(maxLat).9f) union '
        qstring += 'select n.* from plrpExplorer_note n, plrpExplorer_newassetposition b where (n.new_asset_position_id = b.id) and '
        qstring += '(b.longitude<=%(maxLon).9f and b.longitude>=%(minLon).9f) and '
        qstring += '(b.latitude>=%(minLat).9f and b.latitude<=%(maxLat).9f);'
  
        result = qstring % (settings.XGDS_NOTES_NOTE_MODEL, settings.GEOCAM_TRACK_PAST_POSITION_MODEL, bounds)
        return result
    
    def getPosition(self):
        # IMPORTANT this should not be used across multitudes of notes, it is designed to be used during construction.
#         if not self.position:
#             self.position = getClosestPosition(timestamp=self.event_time)
        return self.position
    
    class Meta:
        abstract = True
        ordering = ['event_time']
        permissions = (
            ('edit_all_notes', 'Can edit notes authored by others.'),
        )


class LocatedNote(AbstractLocatedNote):
    position = DEFAULT_POSITION_FIELD()
    tags = DEFAULT_TAGGABLE_MANAGER()

class NoteLinksMixin(object):
    """ extend NoteLinksMixin to properly show up in the notes list table.
    Object should also be extending SearchableModel.
    """
    @property
    def thumbnail_image_url(self):
        return None
    
    def thumbnail_time_url(self, event_time):
        return self.thumbnail_image_url

    def view_time_url(self, event_time):
        return self.view_url
    
class NoteMixin(object):
    """ If your model has notes on it, it should extend NoteMixin.
    """
    @property
    def notes(self):
        ctype = ContentType.objects.get_for_model(self.__class__)
        Note = LazyGetModelByName(getattr(settings, 'XGDS_NOTES_NOTE_MODEL'))

        try:
            return Note.get().objects.filter(content_type__pk = ctype.id, object_id=self.pk)
        except:
            return None
