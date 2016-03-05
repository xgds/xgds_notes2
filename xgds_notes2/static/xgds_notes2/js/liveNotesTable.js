
var liveNotes = (function(global, $) {
    var LiveNotesController = klass(function(params) {
        this._liveNotesStreamURL = params.liveNotesStreamURL;
        this._liveNotesURL = params.liveNotesURL;

        this._setup();
        this._loadCurrentNotes();
        
    }).methods({
        _setup: function() {
         // set everything up.
            this._setupSSE();
            this._setupUIListeners();
            this._messageDiv = $("#messageDiv");
            this._theTable = $("#notesTable");
            var _this = this;
            $("#notesDiv").height("250px");
            $("#notesDiv").resize(function() {
                var newHeight = _this._calcDataTableHeight();
                $('div.dataTables_scrollBody').css('height',newHeight);
                _this._theDataTable.fnAdjustColumnSizing();
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
         * Load the current live notes by performing an ajax call.
         */
        _loadCurrentNotes: function() {
            $.ajax({
                url: this._liveNotesURL,
                dataType: 'json',
                success: $.proxy(function(data) {
                    if (_.isUndefined(data) || data.length === 0){
                        this._setMessage("None found.");
                    } else {
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
                    this._theDataTable.fnAddData(data);
                } else {
                    //TODO GET THIS FROM SETTINGS as notes can differ.
//                    this.columns = Object.keys(data[0]);
//                    var hiddenColumns = [ 'id', 'type', 'console_position'];
//                    this.columns = _.difference(this.columns, hiddenColumns);
                    this.columns = ['event_time', 'author', 'content', 'tags', 'depth', 'lat', 'lon', 'flight'];
                    var columnHeaders = this.columns.map(function(col){
                        return { data: col}
                    });
                    var dataTableObj = {
                            data: data,
                            columns: columnHeaders,
                            autoWidth: true,
                            stateSave: false,
                            paging: true,
                            pageLength: 10, 
                            lengthChange: true,
                            ordering: true,
                            order: [[ 0, "desc" ]],
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
                                                   //TODO timezone problem
                                                   return moment(data).format("HH:mm:ss");
                                               },
                                               targets: 0
                                           },
                                           {
                                               render: function ( data, type, row ) {
                                                   splits = data.split("_");
                                                   if (splits.length > 1){
                                                       return splits[splits.length - 1];
                                                   }
                                                   return data;
                                               },
                                               targets: 7
                                           }
                                       ]
                    }
                    this._setupColumnHeaders();
                    this._theDataTable = this._theTable.dataTable( dataTableObj );
                    this._theDataTable.fnAdjustColumnSizing();
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
        LiveNotesController: LiveNotesController
    };
})(window, jQuery);

    
    