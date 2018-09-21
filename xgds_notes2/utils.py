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

from django.db.models import Q
from xgds_notes2.models import HierarchichalTag
from xgds_map_server.models import Place


def buildQueryForTags(fieldname, field, value, hierarchy):
    listval = [int(x) for x in value]
    if not hierarchy:
        return Q(**{fieldname + '__id__in': listval})
    else:
        result = None
        tags = []
        for pk in listval:
            tag = HierarchichalTag.objects.get(pk=pk)
            tags.append(tag)
        for tag in tags:
            tagqs = HierarchichalTag.get_tree(tag)
            qs = Q(**{fieldname + '__in': tagqs})
            if not result:
                result = qs
            else:
                result |= qs
        return result


