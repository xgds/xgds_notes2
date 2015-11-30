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

var theTree;
var tagtreeNode = $("#tagtree");
var addTagDialog = undefined;

var initializeTree = function(data) {
    tagtreeNode.fancytree({
	source: data,
	checkbox: false,
	extensions: ["dnd"],
	autoActivate: false,
	selectMode: 1,
	autoScroll: false,
	imagePath: "/static/xgds_notes/icons/",
	lazyLoad: function(event, data){
	      var node = data.node;
	      url = '/notes/tagsChildrenTree/' + node.key;
	      data.result = {
	        url: url,
	        cache: false
	      };
	  },
	dnd: {
	    autoExpandMS: 400,
	    focusOnClick: true,
	    preventVoidMoves: true, // Prevent dropping nodes 'before self', etc.
	    preventRecursiveMoves: true, // Prevent dropping nodes on own descendants
	    dragStart: function(node, data) {
		return true;
	    },
	    dragEnter: function(node, data) {
		return 'over';
	    },
	    dragDrop: function(node, data) {
		var params = { 'tag_id': data.otherNode.key, 'parent_id': data.node.key};
		$.ajax({url: '/notes/moveTag/',
		    type: 'POST',
		    dataType: 'json',
		    data: params,
		}).success(function() {
		    data.otherNode.moveTo(node, data.hitMode);
		}).error(function(data) {
		    alert(JSON.parse(data.responseText).failed);
		});
	    }
	},
    }); 

    tagtreeNode.contextmenu({
	delegate: "span.fancytree-title",
	menu: [
	       {title: "Add", cmd: "add", uiIcon: "ui-icon-plus"},
	       {title: "Edit", cmd: "edit", uiIcon: "ui-icon-pencil" },
	       {title: "Delete", cmd: "delete", uiIcon: "ui-icon-trash" },
	       {title: "Make Root", cmd: "rootify", uiIcon: "ui-icon-carat-1-ne" }
	       ],
	       beforeOpen: function(event, ui) {
		   var node = $.ui.fancytree.getNode(ui.target);
		   node.setActive();
	       },
	       select: function(event, ui) {
		   var node = $.ui.fancytree.getNode(ui.target);
		   handleCommand(ui.cmd, node);

	       }
    });
    
    theTree = tagtreeNode.fancytree("getTree");
};

var handleCommand = function(command, node) {
    if (command === "delete"){
	var deleteURL = '/notes/deleteTag/' + node.key;
	$.ajax({url: deleteURL,
	    type: 'POST',
	    dataType: 'json'
	}).success(function(data) {
	    node.remove();
	}).error(function(data) {
	    alert(JSON.parse(data.responseText).failed);
	});
    } else if (command === 'rootify'){
	var rootURL = '/notes/makeRoot/' + node.key;
	$.ajax({url: rootURL,
	    type: 'POST',
	    dataType: 'json'
	}).success(function() {
	    node.moveTo(theTree.getRootNode());
	}).error(function(data) {
	    alert(JSON.parse(data.responseText).failed);
	});
    } else {
	showAddTagDialog(command, node);
    }
};

var refreshTree = function() {
    if (!_.isUndefined(theTree)){
	theTree.reload({
	    url: layerFeedUrl
	});
    }
};

function showAddTagDialog(mode, node) {

    if (mode === 'edit') {
	var title = "Edit Tag";
	$('#id_abbreviation').val(node.data['abbreviation']);
	$('#id_name').val(node.data['name']);
	$('#id_description').val(node.data['description']);
	var start_position = node.span.children[node.span.children.length-1];
    } else if (mode == 'add') {
	title="Add Tag";
	document.getElementById("addTagForm").reset();
	start_position = node.span.children[node.span.children.length-1];
    } else if (mode === 'root'){
	title="Add Root Tag";
	document.getElementById("addTagForm").reset();
	start_position = $("#addRootButton");
    }
    $('#title_p').text(title);
    addTagDialog = $('#addTag').dialog({
	dialogClass: 'no-close',
	modal: false,
	resizable: true,
	minWidth: 450,
	closeOnEscape: true,
	buttons: {
	    'Cancel': function() {
		$(this).dialog('close');
	    },
	    'Save': function() {
		doSaveTag(mode, node);
	    }
	},
	position: {
	    my: 'left top',
	    at: 'right bottom',
	    of: start_position
	},
	dialogClass: 'saveAs'
    });
};

function doSaveTag(mode, node){
    // actually save a tag; the node is the parent
    var theForm = $('#addTagForm');
    var postData = theForm.serializeArray();

    if (mode === 'edit') {
	var errorMsg = "Problem editing tag " + node.label;
	var url = "/notes/editTag/" + node.key;
    } else if (mode === 'add'){
	errorMsg = "Problem adding tag " + postData['name'];
	postData.push({'name':'parent_id', 'value':node.key});
	url = "/notes/addTag";
    } else {
	// root
	errorMsg = "Problem adding root tag " + postData['name'];
	url = '/notes/addRootTag';
    }
    $.ajax({url: url,
	type: 'POST',
	dataType: 'json',
	data: postData
    }).success(function(noteJson) {
	if (mode === 'add'){
	    node.addChildren([noteJson])
	} else if (mode === 'edit'){
	    node.fromDict(noteJson);
	} else {
	    theTree.getRootNode().addChildren([noteJson]);
	}
	addTagDialog.dialog('close'); 
    }).error(function(data) {
	alert(JSON.parse(data.responseText).failed);
    });
}
