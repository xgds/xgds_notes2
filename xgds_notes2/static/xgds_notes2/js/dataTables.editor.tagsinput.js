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
    	_this.closeable = true;
    	 
        field._enabled = true;
        field._input = $(
            '<div id="'+Editor.safeId( field.id )+'">'+
            	'<input class="taginput"  id="id_tags" placeholder="Choose tags" type="text" />' +
            '</div>');
        field._taginput = field._input.find(".taginput");

        // hook the input to our tags input
        xgds_notes.initializeInput(field._taginput);

        _this.on('postSubmit', function( e, data, action ){
        	if (_this.displayed()[0] === 'tags'){
        		_this.closeable = true;
        	}
        });
        
        _this.on('open', function( e, node, data ){
        	if (_this.displayed()[0] === 'tags'){
        		_this.closeable = false;
        	}
        });
        
        _this.on('preClose', function( e ){
        	if (_this.displayed()[0] === 'tags'){
            	return _this.closeable;
        	} else {
        		return true;
        	}
        });
     
        return field._input;
    },
 
    get: function ( field ) {
    	var result = field._taginput.tagsinput('items');
    	return result;
    },
 
    set: function ( field, val ) {
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