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
	lazyLoad: function(event, data){
	      var node = data.node;
	      url = '/notes/tagsChildrenTree/' + node.key;
	      data.result = {
	        url: url,
	        cache: false
	      };
	  },
//	  postProcess: function(event, data) {
//	      data.response = data.response.children;
//	    },
	dnd: {
	    autoExpandMS: 400,
	    focusOnClick: true,
	    preventVoidMoves: true, // Prevent dropping nodes 'before self', etc.
	    preventRecursiveMoves: true, // Prevent dropping nodes on own descendants
	    dragStart: function(node, data) {
		return true;
	    },
	    dragEnter: function(node, data) {
		// we only support dropping onto a folder, we don't do reordering
		if (!_.isUndefined(data.node.folder) && (data.node.folder == true)) {
		    return 'over';
		}
		return false;
	    },
	    dragDrop: function(node, data) {
		var params = { 'tag_id': data.otherNode.key, 'parent_id': data.node.key};
		$.ajax({url: '/notes/moveTag/',
		    type: 'POST',
		    dataType: 'json',
		    data: params,
		}).success(function() {
		    data.otherNode.moveTo(node, data.hitMode);
		}).error(function() {
		    alert("Problem moving tag, try again.");
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
	}).success(function() {
	    node.remove();
	}).error(function() {
	    alert("Problem deleting tag " + node.label);
	});
    } else if (command === 'rootify'){
	var rootURL = '/notes/makeRoot/' + node.key;
	$.ajax({url: rootURL,
	    type: 'POST',
	    dataType: 'json'
	}).success(function() {
	    node.moveTo(theTree.getRootNode());
	}).error(function() {
	    alert("Problem making root tag " + node.label);
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
    }).error(function() {
	alert(errorMsg);
    });
}
