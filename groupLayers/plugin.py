# -*- coding: utf-8 -*-
import os
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsLayerTree, QgsLayerTreeGroup
from qgis.core import QgsMapLayerType
from qgis.core import QgsWkbTypes

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

    def treeToGroup(self):
        newTree = {
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
        layerTree = self.iface.layerTreeCanvasBridge().rootGroup()
        self.oldTree = layerTree.clone()
        self.parseTreeRec(layerTree, newTree)
        print(newTree)
        oldLen = len(layerTree.children())
        vectorGroups = []
        for (type, layers) in newTree['vector'].items():
            if layers:
                grp = QgsLayerTreeGroup(type)
                for l in layers:
                    grp.addLayer(l)
                vectorGroups.append(grp)
        if vectorGroups:
            grp = layerTree.addGroup('vector')
            for g in vectorGroups:
                grp.addChildNode(g)
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

    def parseTreeRec(self, treeLeaf, into):
        for el in treeLeaf.children():
            if QgsLayerTree.isLayer(el):
                l = el.layer()
                print(l.type())
                if l.type() == QgsMapLayerType.VectorLayer:
                    print(l.geometryType())
                    if l.geometryType() == QgsWkbTypes.PointGeometry:
                        into['vector']['point'].append(l)
                    elif l.geometryType() == QgsWkbTypes.LineGeometry:
                        into['vector']['line'].append(l)
                    elif l.geometryType() == QgsWkbTypes.PolygonGeometry:
                        into['vector']['polygon'].append(l)
                    elif l.geometryType() == QgsWkbTypes.UnknownGeometry:
                        pass
                    elif l.geometryType() == QgsWkbTypes.NullGeometry:
                        pass
                    else:
                        pass
            elif QgsLayerTree.isGroup(el):
                self.parseTreeRec(el, into)
                
        
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
