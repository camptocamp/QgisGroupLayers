# -*- coding: utf-8 -*-
import os
from qgis.PyQt.QtWidgets import QAction, QDockWidget, QToolBar
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsLayerTree, QgsLayerTreeGroup, QgsLayerTreeLayer
from .groupTypes import groupHierarchies
from .defSelector import DefSelectDialog


class MainPlugin(object):
    def __init__(self, iface):
        self.name = "groupLayers"
        self.iface = iface

    def initGui(self):
        self.action = QAction(
            QIcon(os.path.dirname(os.path.realpath(__file__)) + "/icon.png"),
            u"Group Layers by similar type",
            self.iface.mainWindow()
        )
        self.action.setObjectName("groupAction")
        self.action.setWhatsThis("Group/ungroup layers by type")
        self.action.setStatusTip("Group/ungroup layers by type")
        self.action.setCheckable(True)
        self.action.triggered.connect(self.run)

        # the icon pressed status could be used, but it is already
        # changed when run method is called, so this is ambiguous
        # therefore a dedicated boolean status is used
        self.grouped = False
        self.groupAdditionalTypes = False
        self.defSelection = groupHierarchies.keys().__iter__().__next__()
        self.hierarchyDefinition = groupHierarchies[self.defSelection]

        # add toolbar button and menu item
        layersDock = self.iface.mainWindow().findChild(QDockWidget, "Layers")
        self.layersToolBar = layersDock.widget().layout().itemAt(0).widget()
        assert isinstance(self.layersToolBar, QToolBar)
        self.layersToolBar.addAction(self.action)
        # self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Group Layers", self.action)

        self.defSelector = QAction(
            u"Select hierarchy definitions",
            self.iface.mainWindow()
        )
        self.defSelector.setObjectName("defSelector")
        self.defSelector.triggered.connect(self.selectDefs)
        self.iface.addPluginToMenu("&Group Layers", self.defSelector)

    def unload(self):
        # remove the plugin menu item and icon
        self.iface.removePluginMenu("&Group Layers", self.action)
        self.iface.removePluginMenu("&Group Layers", self.defSelector)
        self.layersToolBar.removeAction(self.action)
        # self.iface.removeToolBarIcon(self.action)

    def selectDefs(self):
        dialog = DefSelectDialog(self.defSelection)
        if dialog.exec_():
            self.defSelection = dialog.comboBox.currentText()
            self.hierarchyDefinition = groupHierarchies[self.defSelection]
            self.groupAdditionalTypes = dialog.checkBox.isChecked()

    def run(self):
        if self.grouped:
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

    def treeToGroup(self):
        self.newTree = {}
        self.initTreeRec(self.hierarchyDefinition['values'], self.newTree)
        layerTree = self.iface.layerTreeCanvasBridge().rootGroup()
        self.oldTree = layerTree.clone()
        self.parseTreeRec(layerTree)
        oldLen = len(layerTree.children())

        ll = self.treeToLayers(self.newTree)
        for l in ll:
            layerTree.addChildNode(l)

        # caution: commented instruction below removes all layers !!
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
                self.sortInto(l, self.newTree, self.hierarchyDefinition)
            elif QgsLayerTree.isGroup(el):
                self.parseTreeRec(el)

    def sortInto(self, layer, destination, definitions):
        if "groupCriteria" in definitions:
            groupValue = layer.__getattribute__(definitions["groupCriteria"])()
            itemFound = False
            for (label, criteria) in definitions["values"].items():
                if groupValue == criteria["value"]:
                    itemFound = True
                    self.sortInto(layer, destination[label], criteria)
            if not itemFound:
                if self.groupAdditionalTypes:
                    groupName = "others"
                else:
                    groupName = str(groupValue)
                try:
                    destination[groupName].append(layer)
                except KeyError:
                    destination[groupName] = [layer]
        else:
            destination.append(layer)

    def treeToLayers(self, sourceTree):
        if isinstance(sourceTree, dict):
            groupContents = []
            for (layerType, layers) in sourceTree.items():
                groupLayers = self.treeToLayers(layers)
                if groupLayers:
                    grp = QgsLayerTreeGroup(layerType)
                    for l in groupLayers:
                        grp.addChildNode(l)
                    groupContents.append(grp)
            return groupContents
        elif isinstance(sourceTree, list):
            return [QgsLayerTreeLayer(l) for l in sourceTree]
        else:
            raise Exception("Tree dictionary has been initialized incorrectly.")
 
