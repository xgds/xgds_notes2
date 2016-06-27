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
	initDetailView: function(data) {
		var otype = data.object_type;
		var oid = data.object_id;
		if (otype != '' && oid != ''){
			if (otype in app.options.searchModels){
				var modelMap = app.options.searchModels[otype];
				// look up data from ajax
				$.ajax({
		            url: '/xgds_map_server/json/' + otype + '/' + oid,
		            dataType: 'json',
		            success: $.proxy(function(incomingData) {
		            	var data = _.object(modelMap.columns, incomingData);
		            	app.trigger('forceDetail', data);
		            }, this),
		            error: $.proxy(function(data){
		            	console.log(data);
		            }, this)
		          });
				
			}
		}
	},
	clearDetailView: function() {
		
	}
});