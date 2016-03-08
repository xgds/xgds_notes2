//__BEGIN_LICENSE__
// Copyright (c) 2015, United States Government, as represented by the
// Administrator of the National Aeronautics and Space Administration.
// All rights reserved.
//
// The xGDS platform is licensed under the Apache License, Version 2.0
// (the "License"); you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
// http://www.apache.org/licenses/LICENSE-2.0.
//
// Unless required by applicable law or agreed to in writing, software distributed
// under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
// CONDITIONS OF ANY KIND, either express or implied. See the License for the
// specific language governing permissions and limitations under the License.
//__END_LICENSE__

var time_input;

function initializeNotesReference(container, app_label, model_type, object_id, event_time, event_timezone){
    container.find('#id_app_label').val(app_label);
    container.find('#id_model_type').val(model_type);
    container.find('#id_object_id').val(object_id);
    container.find('#id_event_time').val(event_time);
    try {
        container.find('#id_event_timezone').val(event_timezone);
    } catch (err) {
    	// may not have a timezone input
    }
}

function initializeNotesForm(addNow) {
//    notes.setTabOrder(['#id_content', '#id_tags_tag', '#save_note', 'fieldset.selects select']);
    
    time_input = $('form#create_note #id_event_time');
    time_input.width(200);
    time_input.css("margin-right", "10px");
    time_input.wrap($('<div id="event_time_controls">')).css({display: 'inline-block'});
    
    $('#id_content').focus(function(e) {
        if (! time_input.attr('value')) {
            $(this).bind('keydown.content_input', function(e) {
                set_event_time();
                $(this).unbind('keydown.content_input');
            });
        }
    }).blur(function(e) { $(this).unbind('keydown.content_input') });
   
    $('input').on('itemAdded', function(event) {
	if (! time_input.attr('value')) {
            set_event_time();
        }
    });
    
    if (addNow){
	time_input.after($('<button name="Now" class="small">Now</button>').click(function(e) {
	    e.preventDefault();
	    set_event_time();
	}));
    }
}


/*
* Automatically set the timestamp when
* the user starts typing a note.
*/

function set_event_time() {
    // Get the current time from the server and populate the event_time input
    
    time_input.attr({disabled: true, value: 'Waiting for server...'});
    $.get(
        server_time_url,
        {},
        function(data) {
            time_input.attr('value', getLocalTimeString(data, serverTimezone));
            time_input.attr({disabled: false});
        },
        'text'
    );
}

function clear_event_time() {
	time_input.attr('value', '');
}
