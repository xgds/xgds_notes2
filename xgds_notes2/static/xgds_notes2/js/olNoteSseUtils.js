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
	olInitialize: function(topics) {
		if (_.isUndefined(topics)){
			topics = ['map_note']; //notesSse.topics;
		}
		notesSse.subscribe(topics, notesSse.olRenderNoteEvent);
		notesSse.getCurrentNotes(notesSse.olRenderNotes);
	},

	getLayer: function() {
		if (_.isUndefined(notesSse.mapLayer)){
			var layers = app.map.map.getLayers();
			layers.forEach(function(l){
				var name = l.get('name');
				if (!_.isUndefined(name) && name == 'Notes'){
					notesSse.mapLayer = l;
				}});
			if (_.isUndefined(notesSse.mapLayer)){
				// make a new one, should never happen
				var mapNotesGroup = new ol.layer.Group();
                mapNotesGroup.name='Notes';
                layers.push(mapNotesGroup);
                notesSse.mapLayer = mapNotesGroup;
			}
		}
		return notesSse.mapLayer;
	},
	doRender: function(notesJsonArray){
		var noteVector = Note.constructElements(notesJsonArray);
		var layer = notesSse.getLayer();
		layer.getLayers().push(noteVector);
	},
	olRenderNoteEvent: function(event){
		try {
			var receivedNote = JSON.parse(event.data);
			notesSse.doRender([receivedNote]);
		} catch(err){
			// bad stuff
		}
	},
	olRenderNotes: function(data){
		notesSse.doRender(data.data);
	}

});