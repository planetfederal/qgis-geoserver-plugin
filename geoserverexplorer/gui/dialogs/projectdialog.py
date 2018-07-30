# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *

class PublishProjectDialog(QDialog):

    def __init__(self, catalog, parent = None):
        super(PublishProjectDialog, self).__init__(parent)
        self.catalog = catalog
        self.workspace = None
        self.ok = False
        self.initGui()


    def initGui(self):

        layout = QVBoxLayout()
        self.setWindowTitle('Publish project')

        verticalLayout = QVBoxLayout()
        horizontalLayout = QHBoxLayout()
        horizontalLayout.setSpacing(30)
        horizontalLayout.setMargin(0)
        workspaceLabel = QLabel('Workspace')
        self.workspaceBox = QComboBox()
        self.workspaces = self.catalog.get_workspaces()
        try:
            defaultWorkspace = self.catalog.get_default_workspace()
            defaultWorkspace.fetch()
            defaultName = defaultWorkspace.dom.find('name').text
        except:
            defaultName = None
        workspaceNames = [w.name for w in self.workspaces]
        self.workspaceBox.addItems(workspaceNames)
        if defaultName is not None:
            self.workspaceBox.setCurrentIndex(workspaceNames.index(defaultName))
        horizontalLayout.addWidget(workspaceLabel)
        horizontalLayout.addWidget(self.workspaceBox)
        verticalLayout.addLayout(horizontalLayout)

        self.destGroupBox = QGroupBox()
        self.destGroupBox.setLayout(verticalLayout)

        verticalLayout = QVBoxLayout()

        horizontalLayout = QHBoxLayout()
        horizontalLayout.setSpacing(30)
        horizontalLayout.setMargin(0)
        groupLabel = QLabel('Global group name')
        self.groupNameBox = QLineEdit()
        self.groupNameBox.setPlaceholderText("[leave empty if no global group should be created]")
        horizontalLayout.addWidget(groupLabel)
        horizontalLayout.addWidget(self.groupNameBox)
        verticalLayout.addLayout(horizontalLayout)

        self.groupGroupBox = QGroupBox()
        self.groupGroupBox.setLayout(verticalLayout)

        layout.addWidget(self.destGroupBox)
        layout.addWidget(self.groupGroupBox)

        self.overwriteBox = QCheckBox()
        self.overwriteBox.setChecked(False)
        self.overwriteBox.setText("Overwrite without asking")
        layout.addWidget(self.overwriteBox)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Close)
        layout.addWidget(self.buttonBox)

        self.setLayout(layout)

        self.buttonBox.accepted.connect(self.okPressed)
        self.buttonBox.rejected.connect(self.cancelPressed)

        self.resize(400,200)


    def okPressed(self):
        self.workspace = self.workspaces[self.workspaceBox.currentIndex()]
        self.overwrite = self.overwriteBox.isChecked()
        self.groupName = self.groupNameBox.text()
        if self.groupName.strip() == "":
            self.groupName = None
        self.ok = True
        self.close()

    def cancelPressed(self):
        self.ok = False
        self.workspace = None
        self.close()

