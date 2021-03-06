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
	allTags:undefined,
	initializeTags: function() {
	    if (xgds_notes.allTags == undefined){
	        xgds_notes.allTags = new Bloodhound({
	    	  datumTokenizer: Bloodhound.tokenizers.obj.whitespace('name'),
	    	  queryTokenizer: Bloodhound.tokenizers.whitespace,
	    	  prefetch: {
	    	      cache: false, // for now while we build up tag library
	    	      ttl: 1,
	    	      url: '/notes/tagsArray.json'
	    	  }
	    	});
	        xgds_notes.allTags.initialize();
	    }
	},
	initializeInput: function(input, maxTags) {
	    if (input == undefined){
	    	input = $('.taginput');
	    }
	    xgds_notes.initializeTags();
	    $(input).tagsinput({
		  itemValue: 'id',
		  itemText: 'name',
		  maxTags: maxTags,
//		  confirmKeys: [13, 188], // this does not work, suggestion is to use comma
		  tagClass: function(item) {
		  	if (!_.isUndefined(item.className)){
				switch (item.className) {
				  case 'connector': return 'tag connector-tag';
				  default: return 'tag label label-info';
				}
			}

			else {
				return 'tag label label-info';
            }
		  },
		  typeaheadjs: {
		    name: 'allTags',
		    displayKey: 'name',
		    source: xgds_notes.allTags.ttAdapter(),
		    templates: {
			    empty: [
			      '<div class="empty-message">',
			        '&nbsp;Tag not found',
			      '</div>'
			    ].join('\n')
			  }
		  }
		});
	}
});