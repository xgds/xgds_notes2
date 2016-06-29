
var recordedNotes = (function(global, $) {
    var RecordedNotesController = klass(function(params) {
    	this._SSE = params.SSE;
    	this._liveNotesStreamURL = params.liveNotesStreamURL;
        this._recordedNotesURL = params.recordedNotesURL;
        this._theDataTable = undefined;
        this.columns = params.columns;
        this._ordering = params.ordering;
        this._divHeight = params.divHeight;
        this._editable = params.editable;
        this._setup();
        this._loadCurrentNotes();
        
    }).methods({
        _setup: function() {
         // set everything up.
        	if (this._SSE){
        		this._setupSSE();
        	}
            this._setupUIListeners();
            this._messageDiv = $("#messageDiv");
            this._theTable = $(".notes_list");
            var _this = this;
            $("#notesDiv").height(this._divHeight);
            $("#notesDiv").resize(function() {
                var newHeight = _this._calcDataTableHeight();
                $('div.dataTables_scrollBody').css('height',newHeight);
                if (_this._theDataTable != undefined){
                	_this._theDataTable.fnAdjustColumnSizing();
                }
            });
        },
        
        /**
         * Setup the event stream for live notes.
         * If EventSource unavailable, fallback to xHR pooling.
         */
        _setupSSE: function() {
            // check if this browser has SSE capability.
            if (global.EventSource) {
                var eventSource = new EventSource(this._liveNotesStreamURL);
                var _this = this;
                eventSource.addEventListener("notes", function(e) {
                    jsonNotes = JSON.parse(e.data);
                    _this._updateContents(jsonNotes);
                });
            }
            else {
                this._setupSSEFallback();
            }
        },

        /**
         * Setup a simple fallback for the SSE capability using a xHR pooling.
         */
        _setupSSEFallback: function() {
            setTimeout(_loadCurrentNotes, 2000);
        },
        /**
         * Setup UI listeners
         */
        _setupUIListeners: function() {
            var _self = this;
        },

        /**
         * Load the recorded notes by performing an ajax call.
         */
        _loadCurrentNotes: function() {
            $.ajax({
                url: this._recordedNotesURL,
                dataType: 'json',
                success: $.proxy(function(data) {
                    if (_.isUndefined(data) || data.length === 0){
                        this._setMessage("None found.");
                    } else {
                        this._jsonNotes = data;
                        this._updateContents(data);
                        this._setMessage("");
                    }
                }, this),
                error: $.proxy(function(data){
                    this._setMessage("No notes.")
                }, this)
              });
        },
        _setMessage: function(message) {
            this._messageDiv.empty();
            this._messageDiv.html(message);
//            console.log(message);
        },
        _getColumnDefs(headers){
        	result = [];
        	for (var i=0; i<headers.length; i++){
        		var heading = headers[i];
        		if (heading == 'zone'){
        			result.push({ render: function ( data, type, row ) {
                                                   return getLocalTimeString(data, row.event_timezone, "z");
                                               },
                                  targets: i
                                  });
        		} else if  (heading == 'event_time'){
        			result.push({ render: function ( data, type, row ) {
                                                   return getLocalTimeString(data, row.event_timezone, "MM/DD/YY HH:mm:ss");
                                               },
                                  targets: i
                                  });
        		} else if (heading == 'tag_names'){
        			result.push({ render: function(data, type, row) {
												if (row['tag_names'].length > 0){
													var result = "";
													for (var i = 0; i < row['tag_names'].length; i++) {
														result = result + '<span class="tag label label-info">' + row['tag_names'][i] + '</span>&nbsp;';
													}
													return result;
												}
												return null;
											},
									targets: i
									});
        		} else if (heading == 'content'){
        			result.push({ width: '60%'
        						});
        		} else if (heading == 'link') {
        			result.push({render: function(data, type, row){
        								if (row['content_url'] != '') {
        									result = '<a href="' + row['content_url'] + '" target="_blank">';
        									if (row['content_thumbnail_url'] != '') {
        										result += '<img src="' + row['content_thumbnail_url'] + '"';
        										if (row['content_name'] != '') {
        											result += 'alt="' + row['content_name'] +'"';
        										}
        										result += '">';
        									} else if (row['content_name'] != ''){
        										result += row['content_name'];
        									} else {
        										result += "Link";
        									}
        									result += '</a>';
        									return result;
        								}
        								return null;
        								},
        						targets: i
        						 })
        		}
        	}
        	
        	return result;
        },
        _updateContents: function(data) {
                if (!_.isUndefined(this._theDataTable)) {
                    this._theDataTable.fnAddData(data[0]);
                } else {
                    var columnHeaders = this.columns.map(function(col){
                    	result = { data: col,
                 		 	   	   title: col};
                    	
                    	if (col == 'content' || col == 'tag_names') {
                    		result['className'] = 'editable';
                    	} 
                        return result;
                    });
                    $.fn.dataTable.moment( DEFAULT_TIME_FORMAT);
                    $.fn.dataTable.moment( "MM/DD/YY HH:mm:ss");
                    var dataTableObj = {
                            data: data,
                            columns: columnHeaders,
                            autoWidth: true,
                            stateSave: false,
                            select: true,
                            paging: true,
                            pageLength: 10, 
                            lengthChange: true,
                            ordering: true,
                            order: [[ 0, this._ordering ]],
                            scrollX: "100%",
                            scrollY:  this._calcDataTableHeight(),
                            lengthMenu: [[10, 20, 40, -1], [10, 20, 40, "All"]],
                            language: {
                                lengthMenu: "Display _MENU_"
                            },
                            columnDefs: this._getColumnDefs(this.columns)
                    }
                    this._setupColumnHeaders();
                    this._theDataTable = this._theTable.dataTable( dataTableObj );
                    this._theDataTable._fnAdjustColumnSizing();
                    if (this._editable){
	                    var editorFields = this.columns.map(function(col){
	                        result = { label: col,
	                   		 		 	name: col}
	                        if (col == 'tag_names'){
	                        	result['type'] = 'tagsinput';
	                        } else if (col == 'content'){
	                        	result['type'] = 'text';
	                        }
	                        return result;

	                    });
	                    this._editor = new $.fn.dataTable.Editor( {
	                    	ajax: '/notes/editNote/_id_',
	                        table: '#' + this._theDataTable.attr('id'), //notes_list',
	                        idSrc:  'pk',
	                        fields: editorFields
	                    });
	                    var _this = this;
	                    $('.notes_list').on( 'click', 'tbody td.editable', function (e) {
	                        _this._editor.inline( this );
	                    } );
                    }
            }
        },
        _setupColumnHeaders: function() {
          this._theTable.append('<thead class="table_header"><tr id="columnRow"></tr></thead>');
          var columnRow = $('#columnRow');
          $.each(this.columns, function(index, col){
              columnRow.append("<th>"+ col +"</th>");
          });
        },
        _calcDataTableHeight : function() {
            var h = Math.floor($("#notesDiv").height()*.8)
            return h  + 'px';
        }
    });

    return {
        RecordedNotesController: RecordedNotesController
    };
})(window, jQuery);

    
    