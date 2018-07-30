# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
from builtins import str
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *
from geoserverexplorer.qgis import layers
from geoserverexplorer.gui.gsnameutils import GSNameWidget, xmlNameFixUp,\
    xmlNameRegexMsg, xmlNameRegex


class StyleFromLayerDialog(QDialog):

    def __init__(self, styles=None, parent = None):
        super(StyleFromLayerDialog, self).__init__(parent)
        self.styles = styles if styles is not None else []
        self.layer = None
        self.name = None
        self.initGui()

    def initGui(self):
        verticalLayout = QVBoxLayout()
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Close)
        self.okButton = buttonBox.button(QDialogButtonBox.Ok)
        self.cancelButton = buttonBox.button(QDialogButtonBox.Close)
        self.setWindowTitle('Create style from layer')

        horizontalLayout = QHBoxLayout()
        horizontalLayout.setMargin(0)
        layerLabel = QLabel('Layer')
        layerLabel.setSizePolicy(
            QSizePolicy(QSizePolicy.Maximum,
                              QSizePolicy.Fixed))
        self.layerBox = QComboBox()
        self.alllayers = [layer.name() for layer in layers.getAllLayers()]
        self.layerBox.addItems(self.alllayers)
        self.layerBox.setMinimumWidth(250)
        horizontalLayout.addWidget(layerLabel)
        horizontalLayout.addWidget(self.layerBox)
        verticalLayout.addLayout(horizontalLayout)

        horizontalLayout = QHBoxLayout()
        horizontalLayout.setMargin(0)
        nameLabel = QLabel('Name')
        nameLabel.setSizePolicy(
            QSizePolicy(QSizePolicy.Maximum,
                              QSizePolicy.Fixed))
        defaultname = ''
        if len(self.alllayers) > 0:
            defaultname = xmlNameFixUp(self.alllayers[0])
        self.nameBox = GSNameWidget(
            namemsg='',
            name=defaultname,
            nameregex=xmlNameRegex(),
            nameregexmsg=xmlNameRegexMsg(),
            names=self.styles,
            unique=False)
        self.nameBox.setMinimumWidth(250)
        horizontalLayout.addWidget(nameLabel)
        horizontalLayout.addWidget(self.nameBox)
        verticalLayout.addLayout(horizontalLayout)

        self.groupBox = QGroupBox()
        self.groupBox.setTitle("")
        self.groupBox.setLayout(verticalLayout)

        layout = QVBoxLayout()
        layout.addWidget(self.groupBox)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

        buttonBox.accepted.connect(self.okPressed)
        buttonBox.rejected.connect(self.cancelPressed)

        self.layerBox.currentIndexChanged[str].connect(self.updateNameBox)
        self.nameBox.nameValidityChanged.connect(self.okButton.setEnabled)
        self.nameBox.overwritingChanged.connect(self.updateButtons)
        self.okButton.setEnabled(self.nameBox.isValid())
        self.updateButtons(self.nameBox.overwritingName())

        self.resize(400,150)

    @pyqtSlot(str)
    def updateNameBox(self, name):
        self.nameBox.setName(xmlNameFixUp(name))

    @pyqtSlot(bool)
    def updateButtons(self, overwriting):
        txt = "Overwrite" if overwriting else "OK"
        self.okButton.setText(txt)
        self.okButton.setDefault(not overwriting)
        self.cancelButton.setDefault(overwriting)

    def okPressed(self):
        self.layer = self.layerBox.currentText()
        self.name = str(self.nameBox.definedName())
        self.close()

    def cancelPressed(self):
        self.layer = None
        self.name = None
        self.close()

class AddStyleToLayerDialog(QDialog):

    def __init__(self, catalog, layer, parent = None):
        super(AddStyleToLayerDialog, self).__init__(parent)
        self.catalog = catalog
        self.layer = layer
        styles = layer.styles
        self.layerstyles = [style.name for style in styles]
        self.layerdefaultstyle = layer.default_style.name \
            if layer.default_style is not None else ''
        self.style = None
        self.default = None
        self.initGui()

    def initGui(self):
        layout = QVBoxLayout()
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Close)
        self.setWindowTitle('Add style to layer')

        horizontalLayout = QHBoxLayout()
        horizontalLayout.setMargin(0)
        styleLabel = QLabel('Style')
        styleLabel.setSizePolicy(
            QSizePolicy(QSizePolicy.Maximum,
                              QSizePolicy.Fixed))
        self.styleBox = QComboBox()
        styles = [style.name for style in self.catalog.get_styles()]
        sm = QStandardItemModel()
        defaultset = False
        for style in styles:
            isdefault = style == self.layerdefaultstyle
            si = QStandardItem(style)
            si.setEnabled(style not in self.layerstyles and not isdefault)
            if not defaultset and isdefault:
                si.setText("{0} [default style]".format(style))
                defaultset = True
            sm.appendRow(si)
        sm.sort(0)
        self.styleBox.setModel(sm)
        horizontalLayout.addWidget(styleLabel)
        horizontalLayout.addWidget(self.styleBox)
        layout.addLayout(horizontalLayout)

        horizontalLayout = QHBoxLayout()
        horizontalLayout.setMargin(0)
        self.checkBox = QCheckBox("Add as default style")
        if not self.layerdefaultstyle:
            self.checkBox.setChecked(True)
            self.checkBox.setEnabled(False)
        horizontalLayout.addWidget(self.checkBox)
        layout.addLayout(horizontalLayout)

        layout.addWidget(buttonBox)
        self.setLayout(layout)

        buttonBox.accepted.connect(self.okPressed)
        buttonBox.rejected.connect(self.cancelPressed)

        self.resize(400,200)

    def okPressed(self):
        self.style = self.catalog.get_styles(self.styleBox.currentText())[0]
        self.default = self.checkBox.isChecked()
        self.close()

    def cancelPressed(self):
        self.style = None
        self.default = None
        self.close()


class PublishStyleDialog(QDialog):

    def __init__(self, catalogs, layername, parent = None):
        super(PublishStyleDialog, self).__init__(parent)
        self.catalogs = catalogs
        self.catalognames = list(catalogs.keys())
        self.layername = layername
        self.catalog = None
        self.name = None
        self.initGui()


    def initGui(self):
        verticalLayout = QVBoxLayout()
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Close)
        self.okButton = buttonBox.button(QDialogButtonBox.Ok)
        self.cancelButton = buttonBox.button(QDialogButtonBox.Close)
        self.setWindowTitle('Publish style')
        horizontalLayout = QHBoxLayout()
        horizontalLayout.setMargin(0)
        catalogLabel = QLabel('Catalog')
        catalogLabel.setSizePolicy(
            QSizePolicy(QSizePolicy.Maximum,
                              QSizePolicy.Fixed))
        self.catalogBox = QComboBox()
        self.catalogBox.addItems(self.catalognames)
        self.catalogBox.setSizePolicy(
            QSizePolicy(QSizePolicy.Expanding,
                              QSizePolicy.Fixed))
        horizontalLayout.addWidget(catalogLabel)
        horizontalLayout.addWidget(self.catalogBox)
        verticalLayout.addLayout(horizontalLayout)

        horizontalLayout = QHBoxLayout()
        horizontalLayout.setMargin(0)
        nameLabel = QLabel('Name')
        nameLabel.setSizePolicy(
            QSizePolicy(QSizePolicy.Maximum,
                              QSizePolicy.Fixed))
        self.nameBox = GSNameWidget(
            namemsg='',
            name=xmlNameFixUp(self.layername),
            nameregex=xmlNameRegex(),
            nameregexmsg=xmlNameRegexMsg(),
            names=[],
            unique=False)
        self.nameBox.setSizePolicy(
            QSizePolicy(QSizePolicy.Expanding,
                              QSizePolicy.Fixed))
        horizontalLayout.addWidget(nameLabel)
        horizontalLayout.addWidget(self.nameBox)
        verticalLayout.addLayout(horizontalLayout)


        self.groupBox = QGroupBox()
        self.groupBox.setTitle("")
        self.groupBox.setLayout(verticalLayout)

        layout = QVBoxLayout()
        layout.addWidget(self.groupBox)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

        buttonBox.accepted.connect(self.okPressed)
        buttonBox.rejected.connect(self.cancelPressed)

        self.catalogBox.currentIndexChanged[str].connect(self.updateCatalogStyles)
        self.nameBox.nameValidityChanged.connect(self.okButton.setEnabled)
        self.nameBox.overwritingChanged.connect(self.updateButtons)

        self.updateCatalogStyles(self.catalogBox.currentText())
        self.okButton.setEnabled(self.nameBox.isValid())
        self.updateButtons(self.nameBox.overwritingName())

        self.resize(400,200)

    @pyqtSlot(bool)
    def updateButtons(self, overwriting):
        txt = "Overwrite" if overwriting else "OK"
        self.okButton.setText(txt)
        self.okButton.setDefault(not overwriting)
        self.cancelButton.setDefault(overwriting)

    @pyqtSlot(str)
    def updateCatalogStyles(self, catname):
        catalog = self.catalogs[catname]
        styles = [style.name for style in catalog.get_styles()]
        self.nameBox.setNames(styles)

    def okPressed(self):
        self.name = str(self.nameBox.definedName())
        self.catalog = str(self.catalogBox.currentText())
        self.close()

    def cancelPressed(self):
        self.catalog = None
        self.name = None
        self.close()
