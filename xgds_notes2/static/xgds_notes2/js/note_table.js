//__BEGIN_LICENSE__
// Copyright (c) 2015, United States Government, as represented by the
// Administrator of the National Aeronautics and Space Administration.
// All rights reserved.
//
// The xGDS platform is licensed under the Apache License, Version 2.0
// (the 'License'); you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
// http://www.apache.org/licenses/LICENSE-2.0.
//
// Unless required by applicable law or agreed to in writing, software distributed
// under the License is distributed on an 'AS IS' BASIS, WITHOUT WARRANTIES OR
// CONDITIONS OF ANY KIND, either express or implied. See the License for the
// specific language governing permissions and limitations under the License.
//__END_LICENSE__

var smallNoteColumns = [{'data': 'author',
						 'render': function(data, type, full) {
							var splits = full['author'].split(' ');
							var initials = '';
							for (var i=0; i < splits.length; i++){
								initials += splits[i].charAt(0);
							}
							return initials;
						}},
					  { 'data': 'content',
						'width': '80%',
						'className': 'editable',
					 	'render': function(data, type, full) {
										return full['content'];
								}
					  },
					  {   'data': 'tags',
						  'className': 'editable',
						  'render': function(data, type, full) {
						if (full['tags'].length > 0){
							var result = '';
							for (var i = 0; i < full['tags'].length; i++) {
								result = result + "<span class='tag label label-info'>" + full['tags'][i] + '</span>&nbsp;';
							}
							return result;
						}
						return null;
					}
				}
];


var noteDefaultOptions = {
		columns: smallNoteColumns,
        lengthChange: true,
        ordering: false,
        scrollY:  200,
        searching: false,
        paging: false,
        info: false,
        language: {
            emptyTable: 'No notes'
          },
        createdRow: function(nRow, aData, iDataIndex) { // add image id to row
    		$(nRow).attr('id', aData['id'])
        }
};

/* 
 * Table View
 */
function setupNotesTable(divID, table, initialData){
	// initialize the table with json of existing data.
	if ( ! $.fn.DataTable.isDataTable( table) ) {
	    noteDefaultOptions['data'] = initialData;
	    var theNotesTable = $(table).dataTable(noteDefaultOptions);
	    //theNotesTable._fnAdjustColumnSizing();
	    if (HAS_DATATABLES_EDITOR){
	    	var editorFields = smallNoteColumns.map(function(col){
                result = { name: col.data}
                if (col.data == 'tags'){
                	result['type'] = 'tagsinput';
                } else if (col.data == 'content'){
                	result['type'] = 'text';
                }
                return result;

            });
            this._editor = new $.fn.dataTable.Editor( {
            	ajax: '/notes/editNote/_id_',
                table: table,
                idSrc:  'pk',
                fields: editorFields
            });
            var _this = this;
            $(table).on( 'click', 'tbody td.editable', function (e) {
                _this._editor.inline( this );
            } );
	    }
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
	// always clears table first.
	if ( $.fn.DataTable.isDataTable( table) ) {
		var dt = $(tbl).dataTable()
		dt.fnClearTable();
	}
    url = '/notes/notes/' + app_label + '/' + model_type + '/' + object_id;
    $.ajax({url: url,
	    type: 'POST',
	    dataType: 'json'
	}).success(function(data) {
	    setupNotesTable(divID, table, data);
	}).error(function(data) {
	    setupNotesTable(divID, table, []);
	});
}