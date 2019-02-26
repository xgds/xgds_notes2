
var recordedNotes = recordedNotes || {};
$.extend(recordedNotes,{
	initialize: function(params) {
		this.SSE = params.SSE;
		this.liveNotesStreamURL = params.liveNotesStreamURL;
		this.recordedNotesURL = params.recordedNotesURL;
		this.theDataTable = undefined;
		this.columns = params.columns;
		this.ordering = params.ordering;
		this.divHeight = params.divHeight;
		this.editable = params.editable;
		this.setup();
		this.loadCurrentNotes();
	},
	setup: function() {
		// set everything up.
		if (this.SSE){
			this.setupSSE();
		}
		this.setupUIListeners();
		this.messageDiv = $("#messageDiv");
		this.theTable = $(".notes_list");
		var _this = this;
		$("#notesDiv").height(this.divHeight);
		$("#notesDiv").resize(function() {
			var newHeight = _this.calcDataTableHeight();
			$('div.dataTables_scrollBody').css('height',newHeight);
			if (_this.theDataTable != undefined){
				_this.theDataTable.fnAdjustColumnSizing();
			}
		});
	},

	/**
	 * Setup the event stream for live notes.
	 * If EventSource unavailable, fallback to xHR pooling.
	 */
	setupSSE: function() {
		// check if this browser has SSE capability.
		if (global.EventSource) {
			var eventSource = new EventSource(this.liveNotesStreamURL);
			var _this = this;
			eventSource.addEventListener("notes", function(e) {
				jsonNotes = JSON.parse(e.data);
				_this.updateContents(jsonNotes);
			});
		}
		else {
			this.setupSSEFallback();
		}
	},

	/**
	 * Setup a simple fallback for the SSE capability using a xHR pooling.
	 */
	setupSSEFallback: function() {
		setTimeout(_loadCurrentNotes, 2000);
	},
	/**
	 * Setup UI listeners
	 */
	setupUIListeners: function() {
		var _self = this;
	},

	/**
	 * Load the recorded notes by performing an ajax call.
	 */
	loadCurrentNotes: function() {
		$.ajax({
			url: this.recordedNotesURL,
			dataType: 'json',
			success: $.proxy(function(data) {
				if (_.isUndefined(data) || data.length === 0){
					this.setMessage("None found.");
				} else {
					this.jsonNotes = data;
					this.updateContents(data);
					this.setMessage("");
				}
			}, this),
			error: $.proxy(function(data){
				this.setMessage("No notes.")
			}, this)
		});
	},
	setMessage: function(message) {
		this.messageDiv.empty();
		this.messageDiv.html(message);
//		console.log(message);
	},
	getColumnDefs(headers){
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
							result = result + '<span class="tag label label-info">' + row['tag_names'][i] + '</span> ';
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
	updateContents: function(data) {
		if (!_.isUndefined(this.theDataTable)) {
			this.theDataTable.fnAddData(data[0]);
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
					order: [[ 0, this.ordering ]],
					scrollX: "100%",
					scrollY:  this.calcDataTableHeight(),
					lengthMenu: [[5, 10, 20, 40, -1], [5, 10, 20, 40, "All"]],
					language: {
						lengthMenu: "Display _MENU_"
					},
					columnDefs: this.getColumnDefs(this.columns)
			}
			this.setupColumnHeaders();
			this.theDataTable = this.theTable.dataTable( dataTableObj );
			this.theDataTable.fnAdjustColumnSizing();
			if (this.editable){
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
				this.editor = new $.fn.dataTable.Editor( {
					ajax: '/notes/editNote/_id_',
					table: '#' + this.theDataTable.attr('id'), //notes_list',
					idSrc:  'pk',
					fields: editorFields
				});
				var _this = this;
				$('.notes_list').on( 'click', 'tbody td.editable', function (e) {
					_this.editor.inline( this );
				} );
			}
		}
	},
	setupColumnHeaders: function() {
		this.theTable.append('<thead><tr id="columnRow"></tr></thead>');
		var columnRow = $('#columnRow');
		$.each(this.columns, function(index, col){
			columnRow.append("<th>"+ col +"</th>");
		});
	},
	calcDataTableHeight : function() {
		var h = Math.floor($("#notesDiv").height()*.8)
		return h  + 'px';
	}
});
