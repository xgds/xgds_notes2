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

var options = {
        url: note_submit_url, // override for form's 'action' attribute
        type: 'post',       // 'get' or 'post', override for form's 'method' attribute
        dataType: 'json',   // 'xml', 'script', or 'json' (expected server response type)
        timeout: 3000
};

function showSuccess(errorMessage, parent) {
    parent.find('#error_content').text(errorMessage);
    parent.find('#error_icon').removeClass();
    parent.find('#error_icon').addClass('ui-icon');
    parent.find('#error_icon').addClass('ui-icon-circle-check');
    parent.find('#error_div').show();
}

function showError(errorMessage, parent) {
    parent.find('#error_content').text(errorMessage);
    parent.find('#error_icon').removeClass();
    parent.find('#error_icon').addClass('ui-icon');
    parent.find('#error_icon').addClass('ui-icon-circle-close');
    parent.find('#error_div').show();
}

function hideError(parent) {
    parent.find('#error_div').hide();
}

/*
 * Form submission
 *
 */
function finishNoteSubmit(context) {
    var parent = $(context).closest('form');
    var containerDiv = parent.parent().parent();
    
    // validate and process form here
    var content_text = parent.find('textarea#id_content');
    var content = content_text.serialize(); 
    var contentVal = content_text.val();

    hideError(containerDiv);
    var tagInput = parent.find('input#id_tags');
    var tags = tagInput.val();

    if ((content == '') && (tags == '')) {
        content_text.focus();
        showError('Note must not be empty.');
        return false;
    }
    var extras = parent.find('input#id_extras').val();
    var dataString = content + '&tags=' + tags + '&extras=' + extras;
    dataString = dataString + '&object_id=' + parent.find('#id_object_id').val();
    dataString = dataString + '&app_label=' + parent.find('#id_app_label').val();
    dataString = dataString + '&model_type=' + parent.find('#id_model_type').val();
    dataString = dataString + '&position_id=' + parent.find('#id_position_id').val();
    
    var event_hidden = parent.find('#id_event_time');
    var event_timestring = event_hidden.val();
    try {
        if (event_timestring !== undefined){
            dataString = dataString + '&event_time=' + event_timestring;
            try {
            	var timezone_hidden = parent.find('#id_event_timezone');
            	dataString = dataString + "&event_timezone=" + timezone_hidden.val();
            } catch(err){
            	// no timezone
            }
        } else {
            dataString = dataString + "&serverNow=true";
        }
    }
    catch(err) {
        dataString = dataString + "&serverNow=true";
    }
    
    $.ajax({
        type: 'POST',
        url: note_submit_url,
        data: dataString,
        success: function(data) {
    	var content = data[0].content;
    	if (content.length > 30){
    	    content = content.substring(0, 30);
    	}
            showSuccess('Saved ' + content, containerDiv);
            content_text.val('');
            tagInput.tagsinput('removeAll');
            var theNotesTable = containerDiv.find('table#notes_list');
            if (theNotesTable.length > 0){
                if ( !$.fn.DataTable.isDataTable( theNotesTable) ) {
            	setupNotesTable(containerDiv.id, theNotesTable, data[0]);
                } else {
            	theNotesTable.dataTable().fnAddData(data[0]);
                }
            }
        },
        error: function(jqXHR, textStatus, errorThrown) {
            if (errorThrown == '' && textStatus == 'error') {
                showError('Lost server connection', containerDiv);
            } else {
                showError(textStatus + ' ' + errorThrown, containerDiv);
            }
            console.log(jqXHR.getAllResponseHeaders());
        }

    });
}

function hookNoteSubmit() {
    $('.noteSubmit').on('click', function(e) {
    	e.preventDefault();
    	if (!user_session_exists){
    		editUserSession('finishNoteSubmit', this);
    	} else {
    		finishNoteSubmit(this);
    	}
    });
}

function setupNotesUI(){
    var $noteElems = $(".noteinput");
    $noteElems.resizable();
    
    var $tagsElems = $(".tagsinput");
    $tagsElems.resizable();
    
    hookNoteSubmit();
    
    if (!_.isUndefined(xgds_video.displaySegments)){
        for (var source in xgds_video.displaySegments) {
            toggleNoteInput(source);
        }
    } 
    
}

function toggleNoteInput(sourceName){
    var sectionName = "#" + sourceName + "_noteInput";
    $(sectionName).toggle();
    
}
