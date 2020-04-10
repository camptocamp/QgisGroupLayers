import os
import json
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog
from .groupTypes import groupHierarchies

DEFWIDGET, DEFBASE = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'defSelector.ui'))


class DefSelectDialog(DEFWIDGET, DEFBASE):

    def __init__(self, selection=None):
        """
        Initialisation de ComplexeStringDialog
        """
        QDialog.__init__(self)
        self.setupUi(self)
        self.comboBox.addItems(groupHierarchies.keys())
        if selection and selection in groupHierarchies.keys():
            self.comboBox.setCurrentText(selection)
        self.comboBox.currentTextChanged.connect(self.updateText)
        self.updateText(self.comboBox.currentText())

    def updateText(self, text):
        self.textEdit.setPlainText(json.dumps(groupHierarchies[text],
                                              indent=4, default=str))
