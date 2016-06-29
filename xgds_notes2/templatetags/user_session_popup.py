# __BEGIN_LICENSE__
#Copyright (c) 2015, United States Government, as represented by the 
#Administrator of the National Aeronautics and Space Administration. 
#All rights reserved.
# __END_LICENSE__

import itertools

from django import template
from django.conf import settings
from xgds_notes2.forms import UserSessionForm
register = template.Library()

@register.inclusion_tag('xgds_notes2/user_session_popup.html', takes_context=True)
def show_user_session_popup(context):
    defaults = {}
    if hasattr(context['user'], 'preferences'):
        empty_form = UserSessionForm()  # Used as a source of enum choices
        for fieldname in empty_form.fields:
            if 'default_' + fieldname in itertools.chain(context['user'].preferences.keys(), getattr(settings, 'DEFAULT_USER_PREFERENCES', [])):
                value = context['user'].preferences.get('default_' + fieldname)
                defaults[fieldname] = value
    form = UserSessionForm(initial=defaults)
    return { 'form': form }
