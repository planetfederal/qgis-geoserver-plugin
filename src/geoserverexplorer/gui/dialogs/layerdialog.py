from PyQt4 import QtGui, QtCore

from geoserverexplorer.qgis import layers as qgislayers
from geoserverexplorer.gui.gsnameutils import GSNameWidget, xmlNameFixUp, \
    xmlNameRegexMsg, xmlNameRegex

class PublishLayersDialog(QtGui.QDialog):

    def __init__(self, catalog, parent = None):
        super(QtGui.QDialog, self).__init__(parent)
        self.catalog = catalog
        self.layers = qgislayers.getAllLayers()
        self.columns = []
        self.nameBoxes = []
        self.topublish = None
        self.lyr = "Layer"
        self.wrksp = "Workspace"
        self.ow = "Overwrite"
        self.name = "Name"
        self.initGui()


    def initGui(self):
        self.resize(900, 500)
        layout = QtGui.QVBoxLayout()
        self.setWindowTitle('Publish layers')
        self.table = QtGui.QTableWidget(None)

        self.columns = [self.lyr, self.wrksp, self.ow, self.name]

        self.table.setColumnCount(len(self.columns))
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setVisible(True)
        self.table.setHorizontalHeaderLabels(self.columns)
        self.table.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.setTableContent()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setDefaultSectionSize(150)
        self.table.horizontalHeader().setMinimumSectionSize(100)
        self.table.setColumnWidth(self.getColumn(self.name), 140)
        self.table.setColumnWidth(self.getColumn(self.ow), 100)
        self.table.verticalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)
        self.table.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        layout.addWidget(self.table)

        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        self.okButton = self.buttonBox.button(QtGui.QDialogButtonBox.Ok)
        self.cancelButton = self.buttonBox.button(QtGui.QDialogButtonBox.Cancel)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)

        self.buttonBox.accepted.connect(self.okPressed)
        self.buttonBox.rejected.connect(self.cancelPressed)

        self.validateNames()  # so OK button is initially updated

    def getColumn(self, name):
        if name not in self.columns:
            return None
        return self.columns.index(name)

    def setTableContent(self):
        self.table.setRowCount(len(self.layers))
        catlayers = [lyr.name for lyr in self.catalog.get_layers()]
        for idx, layer in enumerate(self.layers):

            lyritem = QtGui.QTableWidgetItem(layer.name())
            lyritem.setToolTip(layer.name())
            lyritem.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable)
            lyritem.setCheckState(QtCore.Qt.Unchecked)
            self.table.setItem(idx, self.getColumn(self.lyr), lyritem)

            nameBox = GSNameWidget(
                name=xmlNameFixUp(layer.name()),
                nameregex=xmlNameRegex(),
                nameregexmsg=xmlNameRegexMsg(),
                names=catlayers,
                unique=False)
            self.table.setCellWidget(idx, self.getColumn(self.name), nameBox)

            self.nameBoxes.append(nameBox)

            overwriteBox = QtGui.QCheckBox()
            overwriteBox.setEnabled(False)
            overwriteBox.setToolTip("Overwrite existing layer")
            self.table.setCellWidget(idx, self.getColumn(self.ow), overwriteBox)

            nameBox.nameValidityChanged.connect(self.validateNames)
            nameBox.overwritingChanged[bool].connect(overwriteBox.setChecked)
            overwriteBox.setChecked(nameBox.overwritingName())  # initial update

            workspaceBox = QtGui.QComboBox()
            workspaceBox.setSizePolicy(
                QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum,
                                  QtGui.QSizePolicy.Fixed))
            workspaces = self.catalog.get_workspaces()
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
            print idx, self.getColumn(self.lyr)
            lyrItem = self.table.item(idx, self.getColumn(self.lyr))
            if lyrItem.checkState() == QtCore.Qt.Checked:
                nameBox = self.table.cellWidget(idx, self.getColumn(self.name))
                layername = nameBox.definedName()
                workspaceBox = self.table.cellWidget(idx, self.getColumn(self.wrksp))
                workspaces = self.catalog.get_workspaces()
                workspace = workspaces[workspaceBox.currentIndex()]
                self.topublish.append((layer, workspace, layername))
        if not bool(self.topublish):
            ret = QtGui.QMessageBox.warning(self, "No layers selected", "You haven't selected any layer to be published\n"
                                      "Are you sure you want to proceed?", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            if not ret:
                return
        self.close()

    def cancelPressed(self):
        self.topublish = None
        self.close()
