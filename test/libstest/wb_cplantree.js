Array.prototype.insert = function(index, item) {
	this.splice(index, 0, item);
};

Array.prototype.foreach = function(f, arg) {
	for (var i = 0; i < this.length; i += 1) {
		var fr = f(i, this[i], arg)
		if (undefined != fr)
			return fr
	}
}

treeTool = {
	treeRootId : 0,
	isNew : true,
	nid : -1,
	isInitTree: false,
	getTreeNodeData : function(fnid) {
		var nodesData = CTestPlanAPi.getCtreeRoot(fnid)
		for ( var i in nodesData) {
			var n = nodesData[i]
			n['text'] = n['name']
			n['state'] = 'closed'
		}
		return nodesData
	},
	initTree : function() {
		var condition = DataOperation.GetCondition()

		$('#folder-list').tree({
			animate : true,
			data : treeTool.getTreeNodeData(treeTool.treeRootId),
			onSelect : function(node){
				if(treeTool.isInitTree){
					treeTool.setNodeLayer(node)
					treeTool.tree = node
					$(this).tree('expand', node.target)
				}else{
					var p = node
					var tn = []
					while(p){
						tn.insert(0,p.nid)
						p = $(this).tree('getParent',p.target)
					}
					window.location.href = window.location.pathname + "?tree=" + tn.join(",")
				}
			},
			onDblClick : function(node) {
				treeTool.setNodeLayer(node)
				if (node.state == "open")
					$(this).tree('collapse', node.target)
				else
					$(this).tree('expand', node.target)
			},
			onBeforeExpand : function(node) {
				if (node.children == undefined)
					$(this).tree('append', {
						parent : node.target,
						data : treeTool.getTreeNodeData(node.nid)
					});
			},
			onContextMenu : function(e, node) {
				e.preventDefault();
				treeTool.tree = node
				if (treeTool.isTestPlan)
					$('#treePlanMenu').menu('show', {
						left : e.pageX,
						top : e.pageY
					});
				else
					$('#treeMenu').menu('show', {
						left : e.pageX,
						top : e.pageY
					});
			},
			onLoadSuccess: function(){
				if(condition.tree){
					setTimeout(treeTool.expandTree, 2, condition.tree)
					condition.tree = undefined
				}
			}
		})
	},
	expandTree: function(treeNodes){
		var ftr = $('#folder-list')
		var targets = ftr.tree("getRoots")
		treeTool.isInitTree = true
		treeNodes.split(",").foreach( function(i,nid){
			targets.foreach(function(i,node){
				if(nid == ""+node.nid){
					ftr.tree("select", node.target)
					targets = ftr.tree("getChildren",node.target)
				}
			})
		})
		setTimeout(treeDataTool.loadTreeDataList,1)
		treeTool.isInitTree = false
	},
	setNodeLayer: function(node){
		var pnode = $('#folder-list').tree('getParent',node.target)
		if(pnode){
			node.tlayer = pnode.tlayer+1
			if(node.tlayer==2)
				treeTool.nid2 = node.nid
		}else{
			treeTool.nid1 = node.nid
			treeTool.nid2 = undefined
			node.tlayer = 1
		}
	},
	deleteTreeNode : function() {
		$.messager.confirm('目录', '确定删除目录', function(r){
			if (r){
				CTestPlanAPi.deleteCtree(treeTool.tree.nid)
				treeTool.initTree()
			}
		});
	},
	showTreeNode : function(isNew) {
		$('#treeAdd').dialog('open')
		if (isNew)
			$("#treeName").val("")
		else
			$("#treeName").val(treeTool.tree.name)
		treeTool.isNew = isNew
		var fnid = treeTool.nid
	},
	saveTreeNode : function() {
		var name = $("#treeName").val()
		if(isRootTree.checked){
			CTestPlanAPi.saveCtree(name, treeTool.treeRootId)
		}
		else if (treeTool.isNew)
			CTestPlanAPi.saveCtree(name, treeTool.tree ? treeTool.tree.nid : treeTool.treeRootId)
		else
			CTestPlanAPi.saveCtree(name, treeTool.tree.fnid, treeTool.tree.nid)
		$('#treeAdd').dialog('close')
		treeTool.initTree()
	},
	getDataByName: function(datas, name, value){
		if(value)
			for (var i = 0; i < datas.total; i += 1) {
				var dataRow = datas.rows[i]
				if (parseInt(dataRow[name]) == parseInt(value)){
						return dataRow
				}
			}
	},
	
	getLoadDataJson: function(dataCols, datas){
		return {
			columns : [ dataCols ],
			data : datas,
			loadFilter : function(data) {
				if (typeof data.length == 'number'
						&& typeof data.splice == 'function') {
					data = {
						total : data.length,
						rows : data
					}
				}
				var dg = $(this);
				var opts = dg.datagrid('options');
				var pager = dg.datagrid('getPager');
				pager.pagination({
					onSelectPage : function(pageNum, pageSize) {
						opts.pageNumber = pageNum;
						opts.pageSize = pageSize;
						pager.pagination('refresh', {
							pageNumber : pageNum,
							pageSize : pageSize
						});
						dg.datagrid('loadData', data);
					}
				});
				if (!data.originalRows) {
					data.originalRows = (data.rows);
				}
				var start = (opts.pageNumber - 1)
						* parseInt(opts.pageSize);
				var end = start + parseInt(opts.pageSize);
				data.rows = (data.originalRows.slice(start, end));
				return data;
			}
		}
	}
}
