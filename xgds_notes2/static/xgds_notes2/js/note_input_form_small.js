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
	options: {
        //url: note_submit_url, // override for form's 'action' attribute
        type: 'post',       // 'get' or 'post', override for form's 'method' attribute
        dataType: 'json',   // 'xml', 'script', or 'json' (expected server response type)
        timeout: 3000
	},
	showSuccess: function(errorMessage, parent) {
	    parent.find('#error_content').html(errorMessage);
	    parent.find('#error_icon').removeClass();
	    parent.find('#error_icon').addClass('fa');
	    parent.find('#error_icon').addClass('fa-check-circle');
	    parent.find('#error_div').show();
	},
	showError: function(errorMessage, parent) {
	    parent.find('#error_content').html(errorMessage);
	    parent.find('#error_icon').removeClass();
	    parent.find('#error_icon').addClass('fa');
	    parent.find('#error_icon').addClass('fa-exclamation-circle');
	    parent.find('#error_div').show();
	},
	hideError: function(parent) {
		var error_div = parent.find('#error_div');
		if (error_div.length > 0){
			error_div.hide();
		}
	},
	getErrorString: function(jqXHR){
		var result = "Save Failed: " + jqXHR.statusText;
		return result;
	},
	getEventTime: function(context) {
		var dataString = "";
		var parent = $(context).closest('.notes_input_container');
		var event_hidden = parent.find('#id_event_time');
	    var event_timestring = event_hidden.val();
	    try {
	        if (event_timestring !== undefined && event_timestring !== ""){
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
	    return dataString;
	},
	findNotesTable: function(containerDiv){
		if (containerDiv.prop('id') == "full_notes_content"){
			var foundTable = $.find('table#searchResultsTable');
    		if (foundTable.length > 0){
    			theNotesTable = $(foundTable[0]);
    			return theNotesTable;
    		}
		}
		var theNotesTable = containerDiv.find('table.notes_list');
        if (theNotesTable.length > 1){
        	theNotesTable = $($(theNotesTable).last());
        } else if (theNotesTable.length == 0){
        	theNotesTable = $.find('table.notes_list');
        	if (theNotesTable.length > 1){
        		theNotesTable = $($(theNotesTable).last())
        	} else if (theNotesTable.length == 0){
        		var foundTable = $.find('table#searchResultsTable');
        		if (foundTable.length > 0){
        			theNotesTable = $(foundTable[0]);
        		}
        	}
        }
        return theNotesTable;
	},
	postSubmit: function(data) {
		// override if you need to do something else after.
	},
	cleanData: function(data, containerDiv){
		// override if you need to change the data;
		return data;
	},
	finishNoteSubmit: function(context) {
			/*
			 * Form submission
			 */
	
	    var parent = $(context).closest('form');
	    var containerDiv = parent.closest('.notes_input_container');
	    
	    // validate and process form here
	    var content_text = parent.find('textarea#id_content');
	    var content = content_text.serialize(); 
	    var contentVal = encodeURIComponent(content_text.val());
	
	    xgds_notes.hideError(containerDiv);
	    var tagInput = parent.find('input#id_tags');
	    var tags = tagInput.val();
	
	    if ((content == '') && (tags == '')) {
	        content_text[0].focus();
	        xgds_notes.showError('Note must not be empty.');
	        return false;
	    }
	    
	    var dataString = content + '&tags=' + tags;
	    var extras = parent.find('input#id_extras').val();
	    if (!_.isEmpty(extras)) {
	    	dataString = dataString + '&extras=' + extras;
	    }
	    dataString = dataString + '&object_id=' + parent.find('#id_object_id').val();
	    dataString = dataString + '&app_label=' + parent.find('#id_app_label').val();
	    dataString = dataString + '&model_type=' + parent.find('#id_model_type').val();
	    var positionVal = parent.find('#id_position_id').val();
	    if (!_.isEmpty(positionVal)){
	    	dataString = dataString + '&position_id=' + positionVal;
	    }
	    var showonmap = parent.find("#id_show_on_map");
	    if (showonmap.length > 0){
	    	if (showonmap[0].checked) {
	    		dataString = dataString + '&show_on_map=1';
	    	}
	    }
	    var keepTags = false;
	    var keepTagsInput = parent.find("#id_keep_tags");
	    if (keepTagsInput.length > 0){
	    	if (keepTagsInput[0].checked) {
	    		keepTags=true;
	    	}
	    }
	    dataString = dataString + xgds_notes.getEventTime(context);
	    
	    var note_submit_url = parent.find("#id_note_submit_url").val();
	    if (_.isUndefined(note_submit_url)){
	    	note_submit_url = '/notes/recordSimple/'
	    }
	    
	    var context = this;
	    $.ajax({
	        type: 'POST',
	        url: note_submit_url,
	        data: dataString,
	        success: function(data) {
		    	var content = data[0].content;
		    	if (content.length > 30){
		    	    content = content.substring(0, 30) + "...";
		    	}
	            xgds_notes.showSuccess('Saved ' + content, containerDiv);
	            xgds_notes.postSubmit(data);
	            content_text.val('');
	            content_text[0].focus();
	            if (!keepTags){
	            	tagInput.tagsinput('removeAll');
	            }
	            if (showonmap.length > 0){
	            	showonmap.prop("checked", false);
	    	    }
	    	    var theNotesTable = undefined;
	            try {
                    theNotesTable = context.findNotesTable(containerDiv);
                } catch (e) {
                    theNotesTable = xgds_notes.findNotesTable(containerDiv);
				}
	            if (!_.isUndefined(theNotesTable) && theNotesTable.length > 0){
	            	theNotesTable.show();
	            	var cleanData = xgds_notes.cleanData(data[0], containerDiv);
	            	var table_id = theNotesTable.attr('id');
	                if ( !$.fn.DataTable.isDataTable( '#'+table_id) ) {
	                	xgds_notes.setupNotesTable(containerDiv.id, theNotesTable, cleanData);
	                } else {
	                	$(theNotesTable).dataTable().fnAddData(cleanData);
	                }
	                xgds_notes.postSubmit(data);
	            } 
	        },
	        error: function(jqXHR, textStatus, errorThrown) {
	            if (errorThrown == '' && textStatus == 'error') {
	                xgds_notes.showError('Lost server connection', containerDiv);
	            } else {
	            	xgds_notes.showError(xgds_notes.getErrorString(jqXHR), containerDiv);
	            }
	        }
	
	    });
	},
	genericFunction: function(path) {
	    return [window].concat(path.split('.')).reduce(function(prev, curr) {
	        return prev[curr];
	    });
	},
	editUserSession: function(nextFunction, context) {
		var edit_user_session_div = $('#edit_user_session_div');
		if (edit_user_session_div.length > 0){
		  edit_user_session_div.dialog({
	        dialogClass: 'no-close',
	        modal: false,
	        resizable: true,
	        width: 400,
	        closeOnEscape: true,
	        title: "Configure Note Recording",
	        buttons: [
	                  {
	                    text: "Cancel",
	                    click: function() {
	                      $( this ).dialog( "close" );
	                    }
	                  },
	                  {
		                    text: "Save",
		                    click: function() {
		                    	var _dialog = this;
		    	            	var theForm = $("#edit_user_session_form");
		    					var postData = theForm.serializeArray();
		    	                $.ajax(
		    		            {
		    		                url: xgds_notes.edit_user_session_ajax, //'/notes/record/session/ajax/'//"{% url 'xgds_notes_edit_user_session_ajax' %}",
		    		                type: "POST",
		    		                data: postData,
		    		                dataType: "json",
		    		                context: $(this),
		    		                success: function(data)
		    		                {
		    		                    user_session_exists=true;
		    		                    $( this ).dialog( "close" );
		    		                    var rlr = $("#roleLocationVehicle");
		    		                    var text = '';
		    		                    if ('role' in data) {
		    		                    	text += data['role'];
										}
		    		                    if ('location' in data) {
		    		                    	text += ', ';
		    		                    	text += data['location'];
										}
		    		                    if ('vehicle' in data) {
		    		                    	text += ', ';
		    		                    	text += data['vehicle'];
										}

		    		                    if (rlr.length > 0){
		    		                  		rlr.text(text);
										}
										xgds_notes.genericFunction(nextFunction)(context, data);

		    		                },
		    		                error: function(data)
		    		                {	
		    		                	alert("Please enter values for all the fields");
		    		                }
		    		            });
		                    }
		                  }
	                ]
	    });
		}
	},
	hookNoteSubmit: function(container) {
		if (container == undefined){
			container = $(document);
		}
		var noteSubmitButton = container.find(".noteSubmit");
		noteSubmitButton.off('click');
		noteSubmitButton.on('click', function(e) {
	    	e.preventDefault();
	    	if (!user_session_exists){
	    		xgds_notes.editUserSession('xgds_notes.finishNoteSubmit', this);
	    	} else {
	    		xgds_notes.finishNoteSubmit(this);
	    	}
	    });
	},
	hookAddNoteButton: function(container) {
		var addNoteButton = undefined;
		if (container === undefined){
			addNoteButton = $('.add_note_button');
		} else {
			addNoteButton = container.find(".add_note_button");
		}
		if (addNoteButton !== undefined) {
			addNoteButton.off('click');
			addNoteButton.on('click',function(event) {
			    event.preventDefault();
			    var tar = $(event.target);
			    var notes_content_div = $(tar.siblings(".notes_content")[0]);
			    if (notes_content_div.length == 1 && notes_content_div[0].id == "add_note_modal") {
			    	if (notes_content_div.is(':visible')){
			    		notes_content_div.modal('hide');
					} else {
			    		notes_content_div.modal('show');
					}
				} else {
                    notes_content_div.show();
                }
                $(notes_content_div.children('.notediv')[0]).toggle()

			});
		}
	},
	setupNotesUI: function(container){
		var input = undefined;
		if (container === undefined){
			input = $('.taginput');
		} else {
			input = container.find('.taginput');
		}
	    xgds_notes.initializeInput(input);
	    xgds_notes.hookNoteSubmit(container);
	    xgds_notes.hookAddNoteButton(container);
	}
});