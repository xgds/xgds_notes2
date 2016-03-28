
var recordedNotes = (function(global, $) {
    var RecordedNotesController = klass(function(params) {
        this._recordedNotesURL = params.recordedNotesURL;
        this.columns = params.columns;
        this._ordering = params.ordering;
        this._divHeight = params.divHeight;
        this._setup();
        this._loadCurrentNotes();
        
    }).methods({
        _setup: function() {
         // set everything up.
            this._setupUIListeners();
            this._messageDiv = $("#messageDiv");
            this._theTable = $("#notesTable");
            var _this = this;
            $("#notesDiv").height(this._divHeight);
            $("#notesDiv").resize(function() {
                var newHeight = _this._calcDataTableHeight();
                $('div.dataTables_scrollBody').css('height',newHeight);
                _this._theDataTable.fnAdjustColumnSizing();
            });
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
                    this._setMessage("Search failed.")
                }, this)
              });
        },
        _setMessage: function(message) {
            this._messageDiv.empty();
            this._messageDiv.html(message);
            console.log(message);
        },
        _addNotes: function(notes){
            console.log(notes);
        },
        _updateContents: function(data) {
                if (!_.isUndefined(this._theDataTable)) {
                    this._theDataTable.fnAddData(data[0]);
                } else {
                    var columnHeaders = this.columns.map(function(col){
                        return { data: col}
                    });
                    $.fn.dataTable.moment( DEFAULT_TIME_FORMAT);
                    var dataTableObj = {
                            data: data,
                            columns: columnHeaders,
                            autoWidth: true,
                            stateSave: false,
                            paging: true,
                            pageLength: 10, 
                            lengthChange: true,
                            ordering: true,
                            order: [[ 0, this._ordering ]],
                            jQueryUI: false,
                            scrollX: "100%",
                            scrollY:  this._calcDataTableHeight(),
                            lengthMenu: [[10, 20, 40, -1], [10, 20, 40, "All"]],
                            language: {
                                lengthMenu: "Display _MENU_"
                            },
                            columnDefs: [
                                           {
                                               render: function ( data, type, row ) {
                                                   return getLocalTimeString(data, row.event_timezone);
                                               },
                                               targets: 0
                                           }
                                       ]
                    }
                    this._setupColumnHeaders();
                    this._theDataTable = this._theTable.dataTable( dataTableObj );
                    this._theDataTable._fnAdjustColumnSizing();
//                    this._theDataTable.columns.adjust().draw();
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

    
    