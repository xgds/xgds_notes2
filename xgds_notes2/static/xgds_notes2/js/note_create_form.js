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

var xgds_notes = xgds_notes || {};
$.extend(xgds_notes,{
	time_input: undefined,
	initializeNotesReference: function(container, app_label, model_type, object_id, event_time, event_timezone){
	    container.find('#id_app_label').val(app_label);
	    container.find('#id_model_type').val(model_type);
	    container.find('#id_object_id').val(object_id);
	    container.find('#id_event_time').val(event_time);
	    try {
	        container.find('#id_event_timezone').val(event_timezone);
	    } catch (err) {
	    	// may not have a timezone input
	    }
	},
	initializeNotesForm: function(addNow) {
	    xgds_notes.time_input = $('form#create_note #id_event_time');
	    //xgds_notes.time_input.width(200);
	    xgds_notes.time_input.css("margin-right", "10px");
	    xgds_notes.time_input.wrap($('<div id="event_time_controls">')).css({display: 'inline-block'});
	    
	    $('#id_content').focus(function(e) {
	        if (_.isEmpty(xgds_notes.time_input.val())) { //}! xgds_notes.time_input.attr('value')) {
	            $(this).bind('keyup.content_input', function(e) {
	                xgds_notes.set_event_time();
	                $(this).unbind('keyup.content_input');
	            });
	        }
	    }).blur(function(e) { $(this).unbind('keyup.content_input') });
	   
	    $('input').on('itemAdded', function(event) {
		if (_.isEmpty(xgds_notes.time_input.val()) ) { //xgds_notes.time_input.attr('value')) {
	            xgds_notes.set_event_time();
	        }
	    });
	    
	    if (addNow){
		xgds_notes.time_input.after($('<button name="Now" id="nowButton" class="small">Now</button>').click(function(e) {
		    e.preventDefault();
		    xgds_notes.set_event_time();
		}));
	    } else {
	    	$("#nowButton").click(function(e) {
			    e.preventDefault();
			    xgds_notes.set_event_time();
			});
	    }
	},
	set_event_time: function() {
		/*
		* Automatically set the timestamp when
		* the user starts typing a note.
		*/
	    // Get the current time from the server and populate the event_time input
		xgds_notes.time_input.val('Waiting for server...');
		xgds_notes.time_input.prop('disabled', true);
//	    xgds_notes.time_input.attr({disabled: true, value: 'Waiting for server...'});
	    $.get(
	        server_time_url,
	        {},
	        function(data) {
	        	xgds_notes.time_input.val(getLocalTimeString(data, serverTimezone));
	            xgds_notes.time_input.prop('disabled', false);
	            //xgds_notes.time_input.attr('value', getLocalTimeString(data, serverTimezone));
	            //xgds_notes.time_input.attr({disabled: false});
	        },
	        'text'
	    );
	},
	clear_event_time: function() {
		try {
			xgds_notes.time_input.val('');
			//xgds_notes.time_input.attr('value', '');
		} catch (err){
			//pass
		}
	}
});
