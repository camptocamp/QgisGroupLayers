# -*- coding: utf-8 -*-
import os
from qgis.PyQt.QtWidgets import QAction, QDockWidget, QToolBar, QToolButton, QMenu, QMessageBox
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsLayerTree, QgsProject, Qgis
from .groupTypes import groupHierarchies
from .defSelector import DefSelectDialog


class MainPlugin(object):
    def __init__(self, iface):
        self.name = "groupLayers"
        self.iface = iface
        self.project = QgsProject.instance()
        self.treeBeforeSave = None

    def initGui(self):
        self.action = QAction(
            QIcon(os.path.dirname(os.path.realpath(__file__)) + "/icon.png"),
            u"Group Layers by similar type (keep visibility)",
            self.iface.mainWindow()
        )
        self.action.setObjectName("groupAction")
        self.action.setWhatsThis("Group/ungroup layers by type")
        self.action.setStatusTip("Group/ungroup layers by type")
        self.action.setCheckable(True)
        self.action.triggered.connect(self.run)

        self.resetAction = QAction("Group and make all layers visible")
        self.resetAction.triggered.connect(self.run_reset_visibility)

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
        self.menuButton = [btn for btn in self.layersToolBar.children()
                           if isinstance(btn, QToolButton)
                           if self.action in btn.actions()][0]
        self.buttonMenu = QMenu()
        self.menuButton.setMenu(self.buttonMenu)
        self.menuButton.setPopupMode(QToolButton.MenuButtonPopup)
        self.buttonMenu.addAction(self.action)
        self.buttonMenu.addAction(self.resetAction)
        # self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Group Layers", self.action)

        self.defSelector = QAction(
            u"Select hierarchy definitions",
            self.iface.mainWindow()
        )
        self.defSelector.setObjectName("defSelector")
        self.defSelector.triggered.connect(self.selectDefs)
        self.iface.addPluginToMenu("&Group Layers", self.defSelector)
        # connect hook to reset the plugin state
        # when a new or existing project is opened
        self.project.cleared.connect(self.reset_state)
        self.project.writeProject.connect(self.write)
        self.project.projectSaved.connect(self.saved)

    def unload(self):
        # remove the plugin menu item and icon
        self.iface.removePluginMenu("&Group Layers", self.action)
        self.iface.removePluginMenu("&Group Layers", self.defSelector)
        self.layersToolBar.removeAction(self.action)
        self.project.cleared.disconnect(self.reset_state)
        self.project.writeProject.disconnect(self.write)
        self.project.projectSaved.disconnect(self.saved)
        try:
            self.project.layerWasAdded.disconnect(self.add_layer_sync)
        except Exception:
            print('could not disconnect add_layer_sync in unload')
        try:
            self.project.layerRemoved.disconnect(self.remove_layer_sync)
        except Exception:
            print('could not disconnect remove_layer_sync in unload')
        # self.iface.removeToolBarIcon(self.action)

    def selectDefs(self):
        dialog = DefSelectDialog(self.defSelection, self.groupAdditionalTypes)
        if dialog.exec_():
            self.defSelection = dialog.comboBox.currentText()
            self.hierarchyDefinition = groupHierarchies[self.defSelection]
            self.groupAdditionalTypes = dialog.checkBox.isChecked()

    def run(self, checked=False, reset=False):
        print('toggle')
        try:
            if self.grouped:
                try:
                    self.project.layerWasAdded.disconnect(self.add_layer_sync)
                except Exception:
                    print('could not disconnect add_layer_sync')
                try:
                    self.project.layerRemoved.disconnect(self.remove_layer_sync)
                except Exception:
                    print('could not disconnect remove_layer_sync')
                self.groupToTree(reset_initial_visibility=reset)
                self.resetAction.setText("Group and make all layers visible")
            else:
                self.treeToGroup(all_visible=reset)
                self.resetAction.setText("Ungroup and restore initial (ungrouped) visibility")
                self.project.layerWasAdded.connect(self.add_layer_sync)
                self.project.layerRemoved.connect(self.remove_layer_sync)
        except Exception as e:
            raise(e)
        finally:
            # synchronize plugin state with button state in case of exceptions
            self.grouped = checked

    def run_reset_visibility(self):
        self.action.toggle()
        self.run(checked=self.action.isChecked(), reset=True)

    def reset_state(self):
        self.action.setChecked(False)
        self.grouped = False

    def write(self):
        if self.grouped:
            answer = QMessageBox.question(self.iface.mainWindow(),
                                          "Save ungrouped state",
                                          "The layers are currently grouped by the "
                                          "groupLayers plugin\n\n"
                                          "Would you like to save the initial (ungrouped) state?\n"
                                          "(save current (grouped) layer tree if answer = NO)",
                                          QMessageBox.Yes | QMessageBox.No)
            if answer == QMessageBox.Yes:
                self.treeBeforeSave = self.iface.layerTreeCanvasBridge().rootGroup().clone()
                self.groupToTree(reset_initial_visibility=True)
                self.iface.messageBar().pushMessage(
                    'CAUTION: The layer tree has been saved in its original format, '
                    'check options if you want to change this behavior.', Qgis.Info
                )

    def saved(self):
        if self.treeBeforeSave is not None:
            tempOldTree = self.oldTree
            self.oldTree = self.treeBeforeSave
            self.groupToTree(reset_initial_visibility=True)
            self.oldTree = tempOldTree
        self.treeBeforeSave = None

    def add_layer_sync(self, addedLayer):
        self.oldTree.addLayer(addedLayer)

    def remove_layer_sync(self, removedLayerId):
        removedLayer = self.oldTree.findLayer(removedLayerId)
        try:
            self.recursiveRemoveFromGroup(self.oldTree, removedLayer)
        except:
            print(f'could not remove layer {removedLayerId} - already removed')

    def recursiveRemoveFromGroup(self, group, layer):
        group.removeChildNode(layer)
        for subGroup in group.findGroups():
            self.recursiveRemoveFromGroup(subGroup, layer)

    def initTreeRec(self, hierarchyDefinition, tree):
        for (k, v) in hierarchyDefinition.items():
            if "groupCriteria" in v:
                tree[k] = {}
                self.initTreeRec(v["values"], tree[k])
            else:
                tree[k] = []

    def treeToGroup(self, all_visible=True):
        self.layerDict = {}
        self.treeRoot = self.project.layerTreeRoot()
        self.initTreeRec(self.hierarchyDefinition['values'], self.layerDict)
        layerTree = self.iface.layerTreeCanvasBridge().rootGroup()
        self.oldTree = layerTree.clone()
        self.parseTreeRec(layerTree)  # into self.layerDict
        self.layerDict = self.cleanTree(self.layerDict)
        oldLen = len(layerTree.children())
        self.layerDictToTree(self.layerDict, layerTree, all_visible)

        # caution: commented instruction below removes all layers !!
        # iface.layerTreeCanvasBridge().rootGroup().clear()
        layerTree.removeChildren(0, oldLen)

    def groupToTree(self, reset_initial_visibility=True):
        self.treeRoot = self.project.layerTreeRoot()
        layerTree = self.iface.layerTreeCanvasBridge().rootGroup()
        oldLen = len(layerTree.children())
        self.insertInto(self.oldTree, layerTree, reset_initial_visibility)
        layerTree.removeChildren(0, oldLen)

    def layerDictToTree(self, layerDict, destinationGroup, all_visible):
        if isinstance(layerDict, dict):
            for (layerType, layers) in layerDict.items():
                grp = destinationGroup.addGroup(layerType)
                self.layerDictToTree(layers, grp, all_visible)
        elif isinstance(layerDict, list):
            for l in layerDict:
                isVisible = self.treeRoot.findLayer(l).isVisible()
                node = destinationGroup.addLayer(l)
                if not all_visible:
                    node.setItemVisibilityChecked(isVisible)

        else:
            raise Exception("Tree dictionary has been initialized incorrectly.")

    def insertInto(self, origin, destination, reset_initial_visibility):
        for el in origin.children():
            if QgsLayerTree.isLayer(el):
                node = destination.addLayer(el.layer())
                node.setItemVisibilityChecked(
                    self.treeRoot.findLayer(el.layer()).isVisible()
                )
            elif QgsLayerTree.isGroup(el):
                node = destination.addGroup(el.name())
                self.insertInto(el, node, reset_initial_visibility)
            if reset_initial_visibility:
                # overwrite visibility with previously saved visibility
                node.setItemVisibilityChecked(el.itemVisibilityChecked())

    def parseTreeRec(self, treeLeaf):
        for el in treeLeaf.children():
            if QgsLayerTree.isLayer(el):
                l = el.layer()
                self.sortInto(l, self.layerDict, self.hierarchyDefinition)
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

    def cleanTree(self, sourceTree):
        # remove all branches without end leaves
        if isinstance(sourceTree, dict):
            groupContents = {}
            for (layerType, layers) in sourceTree.items():
                groupLayers = self.cleanTree(layers)
                if groupLayers:
                    groupContents[layerType] = groupLayers
            return groupContents
        elif isinstance(sourceTree, list):
            return sourceTree
        else:
            raise Exception("Tree dictionary has been initialized incorrectly.")
