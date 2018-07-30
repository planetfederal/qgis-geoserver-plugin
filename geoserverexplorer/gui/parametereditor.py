# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
from builtins import range
from qgis.PyQt import QtCore, QtGui, QtWidgets

class ParameterEditor(QtWidgets.QWidget):
    def __init__(self, settings, explorer):
        self.explorer = explorer
        self.settings = settings
        self.parameters = settings.settings()
        QtWidgets.QWidget.__init__(self)
        self.setupUi()

    def setupUi(self):
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(2)
        layout.setMargin(0)
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setAlternatingRowColors(True)
        self.tree.headerItem().setText(0, "Setting")
        self.tree.headerItem().setText(1, "Value")
        self.tree.setColumnWidth(0, 150)
        layout.addWidget(self.tree)
        for section in self.parameters:
            params = self.parameters[section]
            paramsItem = QtWidgets.QTreeWidgetItem()
            paramsItem.setText(0, section)
            for name, value in params:
                item = QtWidgets.QTreeWidgetItem()
                item.setText(0, name)
                item.setText(1, value)
                item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
                paramsItem.addChild(item)
            self.tree.addTopLevelItem(paramsItem)
        button = QtWidgets.QPushButton()
        button.setText("Save")
        button.clicked.connect(self.saveSettings)
        buttonBox = QtWidgets.QDialogButtonBox()
        buttonBox.setOrientation(QtCore.Qt.Horizontal)
        buttonBox.addButton(button, QtWidgets.QDialogButtonBox.ActionRole)
        layout.addWidget(buttonBox)
        self.setLayout(layout)


    def saveSettings(self):
        parameters = {}
        for i in range(self.tree.invisibleRootItem().childCount()):
            sectionItem = self.tree.invisibleRootItem().child(i)
            sectionParameters = []
            for j in range(sectionItem.childCount()):
                parameterItem = sectionItem.child(j)
                sectionParameters.append((parameterItem.text(0), parameterItem.text(1)))
            parameters[sectionItem.text(0)] = sectionParameters
        self.explorer.run(self.settings.update, "Update settings", [], parameters)


