// __BEGIN_LICENSE__
//Copyright (c) 2015, United States Government, as represented by the 
//Administrator of the National Aeronautics and Space Administration. 
//All rights reserved.
//
//The xGDS platform is licensed under the Apache License, Version 2.0 
//(the "License"); you may not use this file except in compliance with the License. 
//You may obtain a copy of the License at 
//http://www.apache.org/licenses/LICENSE-2.0.
//
//Unless required by applicable law or agreed to in writing, software distributed 
//under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR 
//CONDITIONS OF ANY KIND, either express or implied. See the License for the 
//specific language governing permissions and limitations under the License.
// __END_LICENSE__

var notesSse = notesSse || {};
$.extend(notesSse,{
	topics: ['map_note', 'note'],
	initialize: function(topics) {
		if (_.isUndefined(topics)){
			topics = notesSse.topics;
		}
		notesSse.getChannels();

		//notesSse.subscribe(topics, notesSse.handleNoteEvent);
		//notesSse.getCurrentNotes(notesSse.drawNotes);
	},
	getChannels: function() {
		// get the active channels over AJAX
		if (this.activeChannels === undefined){
			$.ajax({
	            url: '/notes/sseNoteChannels',
	            dataType: 'json',
	            async: false,
	            success: $.proxy(function(data) {
	                this.activeChannels = data;
	            }, this)
	          });
		}
		return this.activeChannels;
	},
	subscribe: function(topics, theFunction) {
		_.each(topics, function(topic){
			sse.subscribe(topic, theFunction, notesSse.getChannels());
		});

	},
	drawNotes: function(data){
		//TODO implement
		console.log(data);
	},
	handleNoteEvent: function(event){
		try {
			var receivedNote = JSON.parse(event.data);
			//TOD draw this somewhere, in the table ...
		} catch(err){
			// bad stuff
		}
	},
	getCurrentNotes: function(theFunction) {
		$.ajax({
            url: '/notes/currentMapNotes.json',
            dataType: 'json',
            success: $.proxy(function(data) {
            	if (!_.isEmpty(data)){
            		theFunction({'data':data});
            	}
            }, this)
          });
	}
});