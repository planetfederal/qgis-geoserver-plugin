# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#

from builtins import range
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *
from geoserverexplorer.qgis import layers as qgislayers
from geoserverexplorer.gui.gsnameutils import GSNameWidget, xmlNameFixUp, \
    xmlNameRegexMsg, xmlNameRegex

class PublishLayersDialog(QDialog):

    def __init__(self, catalog, parent = None):
        super(QDialog, self).__init__(parent)
        self.catalog = catalog
        self.layers = qgislayers.getAllLayers()
        self.columns = []
        self.nameBoxes = []
        self.topublish = None
        self.lyr = "Layer"
        self.wrksp = "Workspace"
        self.ow = "Overwrite"
        self.name = "Name"
        self.style = "Style"
        self.initGui()


    def initGui(self):
        self.resize(900, 500)
        layout = QVBoxLayout()
        self.setWindowTitle('Publish layers')
        self.table = QTableWidget(None)

        self.columns = [self.lyr, self.wrksp, self.style, self.ow, self.name]

        hlayout = QHBoxLayout()
        self.selectAllLabel = QLabel()
        self.selectAllLabel.setText("<a href='#'>Select all</a>")
        self.selectAllLabel.linkActivated.connect(lambda: self.checkLayers(True))
        self.unselectAllLabel = QLabel()
        self.unselectAllLabel.setText("<a href='#'>Unselect all</a>")
        self.unselectAllLabel.linkActivated.connect(lambda: self.checkLayers(False))
        hlayout.addWidget(self.selectAllLabel)
        hlayout.addWidget(self.unselectAllLabel)
        hlayout.addStretch()
        layout.addLayout(hlayout)

        self.table.setColumnCount(len(self.columns))
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setVisible(True)
        self.table.setHorizontalHeaderLabels(self.columns)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setTableContent()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setDefaultSectionSize(150)
        self.table.horizontalHeader().setMinimumSectionSize(100)
        self.table.setColumnWidth(self.getColumn(self.name), 140)
        self.table.setColumnWidth(self.getColumn(self.ow), 100)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        layout.addWidget(self.table)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.okButton = self.buttonBox.button(QDialogButtonBox.Ok)
        self.cancelButton = self.buttonBox.button(QDialogButtonBox.Cancel)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)

        self.buttonBox.accepted.connect(self.okPressed)
        self.buttonBox.rejected.connect(self.cancelPressed)

        self.validateNames()  # so OK button is initially updated

    def checkLayers(self, b):
        state = Qt.Checked if b else Qt.Unchecked
        for idx in range(len(self.layers)):
            lyrItem = self.table.item(idx, self.getColumn(self.lyr))
            lyrItem.setCheckState(state)

    def getColumn(self, name):
        if name not in self.columns:
            return None
        return self.columns.index(name)

    def setTableContent(self):
        styles = self.catalog.get_styles()
        workspaces = self.catalog.get_workspaces()
        self.table.setRowCount(len(self.layers))
        catlayers = [lyr.name for lyr in self.catalog.get_layers()]
        for idx, layer in enumerate(self.layers):

            lyritem = QTableWidgetItem(layer.name())
            lyritem.setToolTip(layer.name())
            lyritem.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            lyritem.setCheckState(Qt.Unchecked)
            self.table.setItem(idx, self.getColumn(self.lyr), lyritem)

            nameBox = GSNameWidget(
                name=xmlNameFixUp(layer.name()),
                nameregex=xmlNameRegex(),
                nameregexmsg=xmlNameRegexMsg(),
                names=catlayers,
                unique=False)
            self.table.setCellWidget(idx, self.getColumn(self.name), nameBox)
            nameBox.setSizePolicy(
                QSizePolicy(QSizePolicy.Maximum,
                                  QSizePolicy.Fixed))
            styleNames = ["[Use QGIS Style]"]
            self.nameBoxes.append(nameBox)

            overwriteBox = QCheckBox()
            overwriteBox.setEnabled(False)
            overwriteBox.setToolTip("Overwrite existing layer")
            self.table.setCellWidget(idx, self.getColumn(self.ow), overwriteBox)

            nameBox.nameValidityChanged.connect(self.validateNames)
            nameBox.overwritingChanged[bool].connect(overwriteBox.setChecked)
            overwriteBox.setChecked(nameBox.overwritingName())  # initial update

            workspaceBox = QComboBox()
            workspaceBox.setSizePolicy(
                QSizePolicy(QSizePolicy.Maximum,
                                  QSizePolicy.Fixed))
            try:
                defaultWorkspace = self.catalog.get_default_workspace()
                defaultWorkspace.fetch()
                defaultName = defaultWorkspace.dom.find('name').text
            except:
                defaultName = None
            workspaceNames = [w.name for w in workspaces]
            workspaceBox.addItems(workspaceNames)
            if defaultName is not None:
                workspaceBox.setCurrentIndex(workspaceNames.index(defaultName))
            self.table.setCellWidget(idx, self.getColumn(self.wrksp), workspaceBox)

            stylesBox = QComboBox()
            styleNames += [s.name for s in styles]
            stylesBox.addItems(styleNames)
            self.table.setCellWidget(idx, self.getColumn(self.style), stylesBox)

    def validateNames(self):
        valid = True
        for namebox in self.nameBoxes:
            if not namebox.isValid():
                valid = False
                break
        self.okButton.setEnabled(valid)

    def okPressed(self):
        self.topublish = []
        for idx, layer in enumerate(self.layers):
            lyrItem = self.table.item(idx, self.getColumn(self.lyr))
            if lyrItem.checkState() == Qt.Checked:
                nameBox = self.table.cellWidget(idx, self.getColumn(self.name))
                layername = nameBox.definedName()
                workspaceBox = self.table.cellWidget(idx, self.getColumn(self.wrksp))
                stylesBox = self.table.cellWidget(idx, self.getColumn(self.style))
                workspaces = self.catalog.get_workspaces()
                styles = self.catalog.get_styles()
                workspace = workspaces[workspaceBox.currentIndex()]
                style = None if stylesBox.currentIndex() == 0 else styles[stylesBox.currentIndex() - 1]
                self.topublish.append((layer, workspace, layername, style))
        if not bool(self.topublish):
            ret = QMessageBox.warning(self, "No layers selected", "You haven't selected any layer to be published\n"
                                      "Are you sure you want to proceed?", QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.No:
                return
        self.close()

    def cancelPressed(self):
        self.topublish = None
        self.close()
