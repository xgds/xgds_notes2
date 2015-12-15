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

function showSuccess(errorMessage) {
    $('#error_content').text(errorMessage);
    $('#error_icon').removeClass();
    $('#error_icon').addClass('ui-icon');
    $('#error_icon').addClass('ui-icon-circle-check');
    $('#error_div').show();
}

function showError(errorMessage) {
    $('#error_content').text(errorMessage);
    $('#error_icon').removeClass();
    $('#error_icon').addClass('ui-icon');
    $('#error_icon').addClass('ui-icon-circle-close');
    $('#error_div').show();
}

function hideError() {
    $('#error_div').hide();
}

/*
 * Form submission
 *
 */
$(function() {
    $('.noteSubmit').on('click', function(e) {
        e.preventDefault();
        var parent = $(this).closest('form');
        // validate and process form here
        var content_text = parent.find('textarea#id_content');
        var content = content_text.serialize(); 
        var contentVal = content_text.val();

        hideError();
        var tagsId = 'input#id_tags';
        var tagInput = parent.find(tagsId);
        var tags = tagInput.val();

//        if (tags == '') {
//            var addtag = parent.find('input#id_tags_tag');
//            // see if we have any contents in the tag that should be created as a tag
//            if (addtag.val() != '' && addtag.val() != 'add a tag') {
//                tagInput.addTag(addtag.val());
//                tags = tagInput.val();
//            }
//        }
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
        try {
            if (event_timestring !== undefined){
                dataString = dataString + '&event_time=' + event_timestring;
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
            success: function(response) {
                var printtime = '';
                try {
                    printtime = response['event_time'];
                    m = moment(new Date(response['event_time']));
                    printtime = m.format("MM/DD/YYYY HH:mm:ss");
                } catch(err) {
                    // pass
                }
                showSuccess('Saved ' + contentVal + ' ' + printtime);
                content_text.val('');
//                tagInput.importTags('');
            },
            error: function(jqXHR, textStatus, errorThrown) {
                if (errorThrown == '' && textStatus == 'error') {
                    showError('Lost server connection');
                } else {
                    showError(textStatus + ' ' + errorThrown);
                }
                console.log(jqXHR.getAllResponseHeaders());
            }

        });
    });
});

/*
 * // pre-submit callback function showRequest(formData, jqForm, options) { //
 * formData is an array; here we use $.param to convert it to a string to
 * display it // but the form plugin does this for you automatically when it
 * submits the data var queryString = $.param(formData); // jqForm is a jQuery
 * object encapsulating the form element. To access the // DOM element for the
 * form do this: // var formElement = jqForm[0];
 *
 * alert('About to submit: \n\n' + queryString); // here we could return false
 * to prevent the form from being submitted; // returning anything other than
 * false will allow the form submit to continue return true; }
 */

//post-submit callback
function showResponse(responseText, statusText, xhr, $form) {
    // for normal html responses, the first argument to the success callback
    // is the XMLHttpRequest object's responseText property

    // if the ajaxForm method was passed an Options Object with the dataType
    // property set to 'xml' then the first argument to the success callback
    // is the XMLHttpRequest object's responseXML property

    // if the ajaxForm method was passed an Options Object with the dataType
    // property set to 'json' then the first argument to the success callback
    // is the json data object returned by the server

    alert('status: ' + statusText + '\n\nresponseText: \n' + responseText +
    '\n\nThe output div should have already been updated with the responseText.');
}

function setupNotesUI(){
    var $noteElems = $(".noteinput");
    $noteElems.resizable();
    
    var $tagsElems = $(".tagsinput");
    $tagsElems.resizable();
    
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
