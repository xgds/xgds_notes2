#!/usr/bin/env python
#  __BEGIN_LICENSE__
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


from time import sleep
from datetime import timedelta
import django
django.setup()

from django.conf import settings
from django.utils import timezone
from geocamUtil.loader import LazyGetModelByName

NOTE_MODEL = LazyGetModelByName(settings.XGDS_NOTES_NOTE_MODEL)

TIME_WINDOW_HOURS = 2


def patch():
    """
    Connect positions with notes
    :return:
    """

    min_time = timezone.now() - timedelta(TIME_WINDOW_HOURS, 'hours')
    notes_without_position = NOTE_MODEL.get().objects.filter(event_time__gte=min_time).exclude(position_found=1)
    for n in notes_without_position:
        position = n.lookupPosition()
        if position:
            n.save()


if __name__ == '__main__':

    while True:
        patch()
        sleep(1)

