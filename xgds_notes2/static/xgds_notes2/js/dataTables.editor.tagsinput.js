// __BEGIN_LICENSE__
//Copyright (c) 2015, United States Government, as represented by the 
//Administrator of the National Aeronautics and Space Administration. 
//All rights reserved.
// __END_LICENSE__

(function ($, DataTable) {
 
if ( ! DataTable.ext.editorFields ) {
    DataTable.ext.editorFields = {};
}
 
var Editor = DataTable.Editor;
var _fieldTypes = DataTable.ext.editorFields;
 
 
_fieldTypes.tagsinput = {
    create: function ( field ) {
    	var _this = this;
    	_this.closeable = false;
    	 
        field._enabled = true;
        field._input = $(
            '<div id="'+Editor.safeId( field.id )+'">'+
            	'<input class="taginput"  id="id_tags" placeholder="Choose tags" type="text" />' +
            '</div>');
        field._taginput = field._input.find(".taginput");

        // hook the input to our tags input
        initializeInput(field._taginput);

        $('button.inputButton', field._input).click( function () {
            if ( field._enabled ) {
                _this.set( field.name, $(this).attr('value') );
            }
     
            return false;
        } );
        
        _this.on('postSubmit', function( e, data, action ){
        	_this.closeable = true;
        });
        
        _this.on('preClose', function( e ){
        	return _this.closeable;
        });
     
        return field._input;
    },
 
    get: function ( field ) {
    	var result = field._taginput.tagsinput('items');
    	return result;
    },
 
    set: function ( field, val ) {
    	this.closeable = false;
    	field._taginput.tagsinput('removeAll');
    	var existing_tags = val;
    	if (existing_tags != undefined){
    		for (var i = 0; i < existing_tags.length; i++){
    			var result = allTags.index.search(existing_tags[i]);
    			field._taginput.tagsinput('add', result[0]);
    		}
    	}
    }
};
 
})(jQuery, jQuery.fn.dataTable);