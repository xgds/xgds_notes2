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

import unicodedata
import traceback
from django.utils import timezone

from django.db import models
from django.db.models.query import QuerySet
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist

from django.template.loader import get_template
from django.template import Context
from django.urls import reverse

from geocamUtil.loader import LazyGetModelByName, getModelByName
from geocamUtil.models import AbstractEnumModel
from geocamUtil.modelJson import modelToDict
from geocamUtil.defaultSettings import HOSTNAME
from geocamUtil.UserUtil import getUserName

from geocamTrack.models import PastResourcePosition
from geocamTrack.utils import getClosestPosition

from treebeard.mp_tree import MP_Node
from taggit.models import TagBase, ItemBase
from taggit.managers import TaggableManager

from xgds_core.models import SearchableModel, BroadcastMixin, HasFlight, HasVehicle, IsFlightChild, IsFlightData
from django.contrib.contenttypes.fields import GenericRelation

from xgds_map_server.models import Place
import json
from django.db.models.signals import post_save
from django.dispatch import receiver
if settings.XGDS_CORE_REDIS:
    from xgds_core.redisUtil import publishRedisSSE

DEFAULT_TAGGED_NOTE_FIELD = lambda: models.ForeignKey(settings.XGDS_NOTES_NOTE_MODEL, related_name='%(app_label)s_%(class)s_related')
DEFAULT_VEHICLE_FIELD = lambda: models.ForeignKey(settings.XGDS_CORE_VEHICLE_MODEL, related_name='%(app_label)s_%(class)s_related',
                                                  verbose_name=settings.XGDS_CORE_VEHICLE_MONIKER, blank=True, null=True)

# TODO if you are using a different default flight field then you will have to customize the Plan Execution
DEFAULT_FLIGHT_FIELD = lambda: models.ForeignKey(settings.XGDS_CORE_FLIGHT_MODEL, null=True, blank=True, related_name='%(app_label)s_%(class)s_related')


class HierarchichalTag(TagBase, MP_Node):
    node_order_by = ['name']
    abbreviation = models.CharField(max_length=8, blank=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    
    def preSave(self):
        self.name = self.name.lower()
        
    def get_tree_json(self):
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


class AbstractTaggedNote(ItemBase):
    """ This is the through table linking tags to notes. """
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
    
    @classmethod
    def buildTagsQuery(cls, search_value):
        splits=search_value.split(' ')
        found_tags = HierarchichalTag.objects.filter(name__in=splits)
        if found_tags:
            return {'tags__in':found_tags}
        return None

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


class AbstractUserSession(models.Model, HasVehicle):
    role = models.ForeignKey(Role)

    @classmethod
    def getFormFields(cls):
        return ['role']
    
    class Meta:
        abstract = True
      

class UserSession(AbstractUserSession):
    location = models.ForeignKey(Location)
    vehicle = DEFAULT_VEHICLE_FIELD()
    
    @classmethod
    def getFormFields(cls):
        return ['role',
                'location']
    

DEFAULT_TAGGABLE_MANAGER = lambda: TaggableManager(through=TaggedNote, blank=True)


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


DEFAULT_NOTES_GENERIC_RELATION = lambda: GenericRelation('xgds_notes2.LocatedNote', related_name='%(app_label)s_%(class)s_related')


class NoteMixin(object):

    """ If your model has notes on it, it should extend NoteMixin.
        You MUST define the GenericRelation to notes for the reverse note search to work.
        To do so, include something like the following
        from django.contrib.contenttypes.fields import GenericRelation
        notes = GenericRelation(MyNoteModel, related_query_name='notes')

    """
    notes = "set to DEFAULT_NOTES_GENERIC_RELATION() or similar in derived classes"


class AbstractMessage(models.Model, SearchableModel, BroadcastMixin, HasFlight, IsFlightChild, IsFlightData,
                      NoteMixin, NoteLinksMixin):
    """
    Abstract base class for simple messages
    """
    event_time = models.DateTimeField(null=True, blank=False, db_index=True)
    event_timezone = models.CharField(null=True, blank=False, max_length=128, default=settings.TIME_ZONE, db_index=True)
    author = models.ForeignKey(User)
    content = models.TextField(blank=True, null=True)

    def get_description(self):
        return self.content

    @classmethod
    def cls_type(cls):
        return settings.XGDS_NOTES_MESSAGE_MODEL_NAME

    @property
    def acquisition_time(self):
        return self.event_time

    @classmethod
    def get_moniker(cls):
        return settings.XGDS_NOTES_MESSAGE_MONIKER

    @classmethod
    def get_plural_moniker(cls):
        return settings.XGDS_NOTES_MESSAGES_MONIKER

    @classmethod
    def get_qualified_model_name(cls):
        return settings.XGDS_NOTES_MESSAGE_MODEL

    @classmethod
    def get_jsmap_key(cls):
        return settings.XGDS_NOTES_MESSAGE_MODEL_NAME

    @classmethod
    def get_object_name(cls):
        return 'XGDS_NOTES_MESSAGE_MODEL'

    @classmethod
    def get_info_json(cls, flight_pk):
        found = LazyGetModelByName(cls.get_qualified_model_name()).get().objects.filter(flight__id=flight_pk)
        result = None
        if found.exists():
            flight = LazyGetModelByName(settings.XGDS_CORE_FLIGHT_MODEL).get().objects.get(id=flight_pk)
            result = {'name': cls.get_plural_moniker(),
                      'count': found.count(),
                      'url': reverse('search_map_object_filter',
                                     kwargs={'modelName': cls.get_jsmap_key(),
                                             'filter': 'flight__group:%d,flight__vehicle:%d' % (
                                             flight.group.pk, flight.vehicle.pk)})
                      }
        return result

    @classmethod
    def get_tree_json(cls, parent_class, parent_pk):
        try:
            found = LazyGetModelByName(cls.get_qualified_model_name()).get().objects.filter(flight__id=parent_pk)
            result = None
            if found.exists():
                moniker = cls.get_plural_moniker()
                flight = found[0].flight
                result = [{"title": moniker,
                           "selected": False,
                           "tooltip": "%s for %s " % (moniker, flight.name),
                           "key": "%s_%s" % (flight.uuid, moniker),
                           "data": {"json": reverse('xgds_map_server_objectsJson',
                                                    kwargs={'object_name': cls.get_object_name(),
                                                            'filter': 'flight__pk:' + str(flight.pk)}),
                                    "sseUrl": "",
                                    "type": 'MapLink',
                                    }
                           }]
            return result
        except ObjectDoesNotExist:
            return None

    @classmethod
    def getSseType(cls):
        return settings.XGDS_NOTES_MESSAGE_SSE_TYPE.lower()

    @property
    def author_name(self):
        return getUserName(self.author)

    # def to_kml(self, animated=False, timestampLabels=False, ignoreLabels=None):
    #     """Define me, or override in your subclass
    #     """
    #     raise NotImplementedError

    @property
    def name(self):
        return self.getLabel()

    def getLabel(self):
        """
        Get the KML note label, use tag if exists or content otherwise
        """
        return self.content[:12]

    @classmethod
    def getSearchableFields(self):
        return ['content', 'author__first_name', 'author__last_name']

    @classmethod
    def getFormFields(cls):
        return ['event_time',
                'content',
                ]

    @classmethod
    def getSearchFormFields(cls):
        return ['content',
                'event_timezone',
                'author',
                # 'flight__vehicle'
                ]

    @classmethod
    def getSearchFieldOrder(cls):
        return ['content',
                'author',
                # 'flight__vehicle',
                'event_timezone',
                'min_event_time',
                'max_event_time']

    def adjustedEventTime(self):
        """
        This is so derived classes can adapt event time for display
        """
        return self.event_time

    def calculateDelayedEventTime(self, raw_time):
        """
        This is so derived classes can adapt event time in the case of being in "delay" mode
        """
        return self.event_time

    def __unicode__(self):
        return "%s: %s %s" % (self.event_time, self.author_name, self.content)

    class Meta:
        abstract = True
        ordering = ['event_time']
        permissions = (
            ('edit_all_messages', 'Can edit messages authored by others.'),
        )


class AbstractNote(AbstractMessage, IsFlightChild):
    """ Abstract base class for notes
    """

    # Override this to specify a list of related fields
    # to be join-query loaded when notes are listed, as an optimization
    # prefetch for reverse or for many to many.
    prefetch_related_fields = ['tags']

    # select related for forward releationships.  
    select_related_fields = ['author', 'role', 'location']

    creation_time = models.DateTimeField(blank=True, default=timezone.now, editable=False, db_index=True)
    modification_time = models.DateTimeField(blank=True, default=timezone.now, editable=False, db_index=True)

    role = models.ForeignKey(Role, null=True)
    location = models.ForeignKey(Location, null=True)

    tags = "set to DEFAULT_TAGGABLE_MANAGER() or similar in any derived classes"
    
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.CharField(max_length=128, null=True, blank=True, db_index=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    @classmethod
    def get_moniker(cls):
        return settings.XGDS_NOTES_NOTE_MONIKER

    @classmethod
    def get_plural_moniker(cls):
        return settings.XGDS_NOTES_MONIKER

    @classmethod
    def get_qualified_model_name(cls):
        return settings.XGDS_NOTES_NOTE_MODEL

    @classmethod
    def get_jsmap_key(cls):
        return settings.XGDS_NOTES_MODEL_NAME

    @classmethod
    def buildTagsQuery(cls, search_value):
        splits = search_value.split(' ')
        found_tags = HierarchichalTag.objects.filter(name__in=splits)
        if found_tags:
            return {'tags__in': found_tags}
        return None

    def getSseType(self):
        return settings.XGDS_NOTES_NOTE_SSE_TYPE

    @property
    def object_type(self):
        if self.content_type:
            return self.content_type.model_class().cls_type()
        return None

    @classmethod
    def cls_type(cls):
        return settings.XGDS_NOTES_MODEL_NAME

    @classmethod
    def get_object_name(cls):
        return 'XGDS_NOTES_NOTE_MODEL'

    @property
    def tag_ids(self):
        return None

    @property
    def tag_names(self):
        result = []
        for tag in self.tags.get_queryset():
            result.append(tag.name)
        if not result:
            return None
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
    
    @classmethod
    def getFormFields(cls):
        return ['event_time',
                'content',
                'tags',
                ]
    
    @classmethod
    def getSearchFormFields(cls):
        return ['content',
                'tags',
                'event_timezone',
                'author',
                'role',
                'location',
                # 'flight__vehicle'
                ]
    
    @classmethod
    def getSearchFieldOrder(cls):
        return ['tags',
                'hierarchy',
                'content',
                'author',
                'role',
                'location',
                # 'flight__vehicle',
                'event_timezone',
                'min_event_time',
                'max_event_time']
        
# For sphinx to work right - these next 2 lines *MUST* be in the inherited concrete
# class. Will fail miserably if it tries to search on this abstract class.
#    if "SphinxSearch" in globals():
#        search = SphinxSearch()

    def getLabel(self):
        """
        Get the KML note label, use tag if exists or content otherwise
        """
        result = self.content[:12]
        if result == "":
            if self.tags:
                result = str(self.tags.first)
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
    
    def thumbnail_time_url(self, event_time):
        return self.content_thumbnail_url
    
    @property
    def content_thumbnail_url(self):
        if self.content_object:
            return self.content_object.thumbnail_time_url(self.event_time)
        return None

    @staticmethod
    def getMapBoundedQuery(minLon, minLat, maxLon, maxLat, today=False):
        """
        Implement this in your note that has a position to return a query that will filter notes by position
        """
        return None

    @classmethod
    def get_tree_json(cls, parent_class, parent_pk):
        """ For some reason because of the way this method is used with reflection we have to redefine it."""
        try:
            found = LazyGetModelByName(cls.get_qualified_model_name()).get().objects.filter(flight__id=parent_pk)
            result = None
            if found.exists():
                moniker = cls.get_plural_moniker()
                flight = found[0].flight
                result = [{"title": moniker,
                           "selected": False,
                           "tooltip": "%s for %s " % (moniker, flight.name),
                           "key": "%s_%s" % (flight.uuid, moniker),
                           "data": {"json": reverse('xgds_map_server_objectsJson',
                                                    kwargs={'object_name': cls.get_object_name(),
                                                            'filter': 'flight__pk:' + str(flight.pk)}),
                                    "sseUrl": "",
                                    "type": 'MapLink',
                                    }
                           }]
            return result
        except ObjectDoesNotExist:
            return None

    @classmethod
    def get_info_json(cls, flight_pk):
        """ For some reason because of the way this method is used with reflection we have to redefine it."""
        found = LazyGetModelByName(cls.get_qualified_model_name()).get().objects.filter(flight__id=flight_pk)
        result = None
        if found.exists():
            flight = LazyGetModelByName(settings.XGDS_CORE_FLIGHT_MODEL).get().objects.get(id=flight_pk)
            result = {'name': cls.get_plural_moniker(),
                      'count': found.count(),
                      'url': reverse('search_map_object_filter',
                                     kwargs={'modelName': cls.get_jsmap_key(),
                                             'filter': 'flight__group:%d,flight__vehicle:%d' % (
                                                 flight.group.pk, flight.vehicle.pk)})
                      }
        return result

    class Meta:
        abstract = True
        ordering = ['event_time']
        permissions = (
            ('edit_all_notes', 'Can edit notes authored by others.'),
        )

    def __unicode__(self):
        # return "%s: %s" % (self.event_time, unicodedata.normalize('NFKD', unicode(self.content, 'utf-8')).encode('ascii','ignore'))
        return "%s: %s" % (self.event_time, self.content)


DEFAULT_POSITION_FIELD = lambda: models.ForeignKey(settings.GEOCAM_TRACK_PAST_POSITION_MODEL, null=True, blank=True, related_name="%(app_label)s_%(class)s_notes_set"  )


class PositionMixin(object):
    """
    Mixin to provide position
    """
    position = "set to DEFAULT_POSITION_FIELD() or similar in derived classes"

    # TODO completely unclear why this cannot be defined here; this should be able to be a models.Model and abstract
    # BUT it makes migrations have all sorts of problems with method resolution order.  So for now duplicating
    # implementation.
    # True if we have searched for the position and found one, False if we searched and did not find one.
    # null if we this field was created after this note existed or we have not tried looking.
    # position_found = models.NullBooleanField(default=None)


class AbstractLocatedNote(AbstractNote, PositionMixin):
    """ This is a basic note with a location, pulled from the current settings for geocam track past position model.
    """
    place = models.ForeignKey(Place, blank=True, null=True, verbose_name=settings.XGDS_MAP_SERVER_PLACE_MONIKER, related_name="%(app_label)s_%(class)s_related")
    show_on_map = models.BooleanField(default=False)  # broadcast this note on the map by default

    # True if we have searched for the position and found one, False if we searched and did not find one.
    # null if we this field was created after this note existed or we have not tried looking.
    position_found = models.NullBooleanField(default=None)

    def getSseType(self):
        if self.show_on_map:
            return settings.XGDS_NOTES_MAP_NOTE_CHANNEL
        else:
            return settings.XGDS_NOTES_NOTE_SSE_TYPE

    @classmethod
    def getFormFields(cls):
        result = super(AbstractLocatedNote, cls).getSearchFormFields()
        result.append('show_on_map')
        return result

    @classmethod
    def getSearchFormFields(cls):
        result = super(AbstractLocatedNote, cls).getSearchFormFields()
        result.append('place')
        return result

    @classmethod
    def getSearchFieldOrder(cls):
        result = super(AbstractLocatedNote, cls).getSearchFieldOrder()
        result.append('place')
        return result

    # def to_kml(self, animated=False, timestampLabels=False, ignoreLabels=None):
    #     if ignoreLabels is None:
    #         ignoreLabels = []
    #     # if no label is associated with the note, we'll fall back to a timetamp-based label anyway.
    #     notelabel = None
    #     if timestampLabels or (hasattr(self, 'label') and self.label and self.label.value in ignoreLabels):
    #         atime = self.adjustedEventTime()
    #         notelabel = "%02d:%02d" % (atime.hour, atime.minute)
    #     else:
    #         notelabel = self.getLabel()
    #
    #     if not notelabel:
    #         atime = self.adjustedEventTime()
    #         try:
    #             altitude = self.position.altitude
    #             notelabel = "%s %02d:%02d" % (altitude, atime.hour, atime.minute)
    #         except:
    #             notelabel = "%02d:%02d" % (atime.hour, atime.minute)
    #
    #     return get_template('xgds_notes2/notes/note.kml').render({
    #         'note': self,
    #         'animated': animated,
    #         'notelabel': notelabel,
    #     })
    #

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

    # TODO IMPORTANT -- now that we have flexible types of positions this has to use that, probably from settings.
    def getPosition(self):
        return self.position

    def lookupPosition(self):
        # IMPORTANT this should not be used across multitudes of notes, it is designed to be used during construction.
        if not self.position:
            track=None
            if hasattr(self, 'flight') and self.flight:
                if hasattr(self.flight, 'track'):
                    track = self.flight.track
            self.position = getClosestPosition(track=track, timestamp=self.event_time)
            return self.position

    class Meta:
        abstract = True
        ordering = ['event_time']
        permissions = (
            ('edit_all_notes', 'Can edit notes authored by others.'),
        )


class LocatedMessage(AbstractMessage, PositionMixin):
    """ This is a simple note to be used for chat messages; it does not support tags or notes on it. """
    position = DEFAULT_POSITION_FIELD()
    flight = DEFAULT_FLIGHT_FIELD()

    # True if we have searched for the position and found one, False if we searched and did not find one.
    # null if we this field was created after this note existed or we have not tried looking.
    position_found = models.NullBooleanField(default=None)

    notes = DEFAULT_NOTES_GENERIC_RELATION()

    @classmethod
    def getSearchFormFields(cls):
        result = super(LocatedMessage, cls).getSearchFormFields()
        result.append('flight__vehicle')
        return result

    @classmethod
    def getSearchFieldOrder(cls):
        result = super(LocatedMessage, cls).getSearchFieldOrder()
        result.append('flight__vehicle')
        return result

# @receiver(post_save, sender=LocatedMessage)
# def publishAfterSave(sender, instance, **kwargs):
#     if settings.XGDS_CORE_REDIS:
#         # TODO this should really be one channel?
#         for channel in settings.XGDS_SSE_NOTE_CHANNELS:
#             publishRedisSSE(channel, settings.XGDS_NOTES_MESSAGE_SSE_TYPE.lower(), json.dumps({}))


class LocatedNote(AbstractLocatedNote):
    """ This is the default note class, which can have tags and can have notes on it."""
    position = DEFAULT_POSITION_FIELD()
    tags = DEFAULT_TAGGABLE_MANAGER()
    notes = DEFAULT_NOTES_GENERIC_RELATION()
    flight = DEFAULT_FLIGHT_FIELD()

    @classmethod
    def getSearchFormFields(cls):
        result = super(LocatedNote, cls).getSearchFormFields()
        result.append('flight__vehicle')
        return result

    @classmethod
    def getSearchFieldOrder(cls):
        result = super(LocatedNote, cls).getSearchFieldOrder()
        result.append('flight__vehicle')
        return result
    
# @receiver(post_save, sender=LocatedNote)
# def publishAfterSave(sender, instance, **kwargs):
#     if settings.XGDS_CORE_REDIS:
#         # TODO this should really be one channel?
#         for channel in settings.XGDS_SSE_NOTE_CHANNELS:
#             publishRedisSSE(channel, settings.XGDS_NOTES_NOTE_SSE_TYPE.lower(), json.dumps({}))

