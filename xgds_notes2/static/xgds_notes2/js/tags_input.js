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

var allTags;

function initializeTags() {
    allTags = new Bloodhound({
	  datumTokenizer: Bloodhound.tokenizers.obj.whitespace('name'),
	  queryTokenizer: Bloodhound.tokenizers.whitespace,
	  prefetch: {
	      cache: false, // for now while we build up tag library
	      ttl: 1,
	      url: '/notes/tagsArray.json'
	  }
	});
    allTags.initialize();
}

function initializeInput() {
    
    $('.taginput').tagsinput({
	  itemValue: 'id',
	  itemText: 'name',
//	  confirmKeys: [13, 44],
	  typeaheadjs: {
	    name: 'allTags',
	    displayKey: 'name',
	    source: allTags.ttAdapter(),
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