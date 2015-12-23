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

var noteColumns = [{ "mRender": function(data, type, full) {
    					return '<strong><small>' + full['author'] + '</small></strong>&nbsp;' + full['content'];
	                               }
		 },
		 { "mRender": function(data, type, full) {
		     if (full['tags'].length > 0){
			 var result = "";
			 for (var i = 0; i < full['tags'].length; i++) {
			     result = result + '<span class="tag label label-info">' + full['tags'][i] + '</span>&nbsp;';
			 }
			 return result;
		     }
		     return null;
		 	}
		 }
	];


var noteDefaultOptions = {
	aoColumns: noteColumns,
        bAutoWidth: true,
        stateSave: true,
        bPaginate: true,
        iDisplayLength: -1, 
        bLengthChange: true,
        bSort: true,
        bJQueryUI: false,
        scrollY:  200,
        searching: false,
        paging: false,
        ordering: false,
        info: false,
        language: {
            emptyTable: "No notes"
          },
        fnCreatedRow: function(nRow, aData, iDataIndex) { // add image id to row
    		$(nRow).attr('id', aData['id'])
        }
};


/* 
 * Table View
 */
function setupNotesTable(divID, table, initialData){
	// initialize the table with json of existing data.
	if ( ! $.fn.DataTable.isDataTable( table) ) {
	    noteDefaultOptions["aaData"] = initialData;
	    var theNotesTable = $(table).dataTable(noteDefaultOptions);
	 // handle resizing
	    var tableResizeTimeout;
		$('#' + divID).resize(function() {
		    // debounce
		    if ( tableResizeTimeout ) {
			clearTimeout( tableResizeTimeout );
		    }

		    tableResizeTimeout = setTimeout( function() {
			updateTableScrollY(divID, table.id);
		    }, 30 );
		});
	} else {
	    // set the data for existing datatable
	    var dt = table.dataTable();
	    dt.fnClearTable();
	    if (initialData.length > 0){
		dt.fnAddData(initialData);
	    }
	}
}

function getNotesForObject(app_label, model_type, object_id, divID, table){
    url = '/notes/notes/' + app_label + '/' + model_type + '/' + object_id;
    $.ajax({url: url,
	    type: 'POST',
	    dataType: 'json'
	}).success(function(data) {
	    setupNotesTable(divID, table, data);
	}).error(function(data) {
	    setupNotesTable(divID, table, []);
	    console.log('no notes');
	});
}