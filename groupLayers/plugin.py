# -*- coding: utf-8 -*-
import os
from collections import defaultdict
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsLayerTree, QgsLayerTreeGroup
from qgis.core import QgsMapLayerType
from qgis.core import QgsWkbTypes
from.groupTypes import groupHierarchy

class MainPlugin(object):
    def __init__(self, iface):
        self.name = "groupLayers"
        self.iface = iface

    def initGui(self):
        # create action that will start plugin configuration
        self.action = QAction(
            QIcon(os.path.dirname(os.path.realpath(__file__)) + "/icon.png"),
            u"Group Layers by similar type",
            self.iface.mainWindow()
        )
        self.action.setObjectName("groupAction")
        self.action.setWhatsThis("Group/ungroup layers by type")
        self.action.setStatusTip("Group/ungroup layers by type")
        self.action.setCheckable(True)
        self.action.setChecked(False)
        print(self.action.isChecked())
        self.action.triggered.connect(self.run)

        # add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Group Layers", self.action)

    def unload(self):
        # remove the plugin menu item and icon
        self.iface.removePluginMenu("&Group Layers", self.action)
        self.iface.removeToolBarIcon(self.action)

    def run(self):
        # create and show a configuration dialog or something similar
        print("groupPlugin: run called!")
        print(self.action.isChecked())
        if not self.action.isChecked():
            self.groupToTree()
            self.grouped = False
        else:
            self.treeToGroup()
            self.grouped = True

    def initTreeRec(self, hierarchyDefinition, tree):
        for (k, v) in hierarchyDefinition.items():
            if "groupCriteria" in v:
                tree[k] = {}
                self.initTreeRec(v["values"], tree[k])
            else:
                tree[k] = []

    def defaultTree(self):
        return {
            'vector': {
                'point': [],
                'line': [],
                'polygon': []
            },
            'raster': {
                'wms': [],
                'wfs': []
            }
        }

    def treeToGroup(self):
        # newTree = self.defaultTree()
        self.newTree = {}
        self.initTreeRec(groupHierarchy['values'], self.newTree)
        print(self.newTree)
        layerTree = self.iface.layerTreeCanvasBridge().rootGroup()
        self.oldTree = layerTree.clone()
        self.parseTreeRec(layerTree)
        #self.parseTreeRecDef(layerTree, groupHierarchy)
        print(self.newTree)
        oldLen = len(layerTree.children())

        # ll = self.treeToLayers(self.newTree)
        # print (ll)
        # for l in ll:
        #     layerTree.addChildNode(l)
        for (label, subtree) in self.newTree.items():
            layers = self.treeToLayers(subtree)
            if layers:
                grp = layerTree.addGroup(label)
                for l in layers:
                    grp.addChildNode(l)
        # removes layers !!
        # iface.layerTreeCanvasBridge().rootGroup().clear()
        layerTree.removeChildren(0, oldLen)

    def groupToTree(self):
        layerTree = self.iface.layerTreeCanvasBridge().rootGroup()
        oldLen = len(layerTree.children())
        self.insertInto(self.oldTree, layerTree)
        layerTree.removeChildren(0, oldLen)

    def insertInto(self, origin, destination):
        for el in origin.children():
            if QgsLayerTree.isLayer(el):
                destination.addLayer(el.layer())
            elif QgsLayerTree.isGroup(el):
                grp = destination.addGroup(el.name())
                self.insertInto(el, grp)

    def parseTreeRec(self, treeLeaf):
        for el in treeLeaf.children():
            if QgsLayerTree.isLayer(el):
                l = el.layer()
                self.sortInto(l, self.newTree, groupHierarchy)
            elif QgsLayerTree.isGroup(el):
                self.parseTreeRec(el)

    def sortInto(self, layer, destination, definitions):
        if "groupCriteria" in definitions:
            groupValue = layer.__getattribute__(definitions["groupCriteria"])()
            for (label, criteria) in definitions["values"].items():
                if groupValue == criteria["value"]:
                    self.sortInto(layer, destination[label], criteria)
        else:
            destination.append(layer)

    def treeToLayers(self, sourceTree):
        groupContents = []
        if isinstance(sourceTree, dict):
            for (layerType, layers) in sourceTree.items():
                groupLayers = self.treeToLayers(layers)
                if groupLayers:
                    grp = QgsLayerTreeGroup(layerType)
                    for l in layers:
                        grp.addLayer(l)
                    groupContents.append(grp)
            return groupContents
        elif isinstance(sourceTree, list):
            return sourceTree
        else:
            raise Exception("Tree dictionary has been initialized incorrectly.")
 

# for el in oldTree.children():
#     if QgsLayerTree.isLayer(el):
#         iface.layerTreeCanvasBridge().rootGroup().addLayer(el.layer())
#     elif QgsLayerTree.isGroup(el):
#         iface.layerTreeCanvasBridge().rootGroup().addGroup(el.name())

# oldTree = layerTree.clone()

# for el in oldTree.children():
#     if QgsLayerTree.isLayer(el):
#         print(el.layer())
#     elif QgsLayerTree.isGroup(el):
#         print(el.name())
