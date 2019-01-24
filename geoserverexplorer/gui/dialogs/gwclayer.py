# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
from builtins import str
from builtins import range
from geoserverexplorer.gui.extentpanel import ExtentSelectionPanel
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *

class EditGwcLayerDialog(QDialog):

    def __init__(self, layers, gwclayer = None):
        QDialog.__init__(self)
        self.setupUi()
        self.setWindowTitle('Define cache layer')
        self.layers = layers
        self.layerBox.addItems([lyr.name for lyr in layers])
        if gwclayer is not None:
            self.layerBox.setEditText(gwclayer.name)
            self.spinBoxHeight.setValue(gwclayer.metaHeight)
            self.spinBoxWidth.setValue(gwclayer.metaWidth)
            checkboxes = [self.checkBox4326, self.checkBox900913, self.checkBoxGlobalPixel, self.checkBoxGlobalScale, self.checkBoxGoogle]
            for checkbox in checkboxes:
                checkbox.setChecked(checkbox.text() in gwclayer.gridsets)
            checkboxes = [self.checkBoxGif, self.checkBoxJpg, self.checkBoxPng, self.checkBoxPng8]
            for checkbox in checkboxes:
                checkbox.setChecked('image/' + checkbox.text() in gwclayer.mimetypes)
        else:
            self.spinBoxHeight.setValue(4)
            self.spinBoxWidth.setValue(4)
            self.checkBox4326.setChecked(True)
            self.checkBoxPng.setChecked(True)
        self.layername = None
        self.formats = None
        self.gridsets = None
        self.metaWidth = None
        self.metaHeight = None

    def setupUi(self):
        self.resize(528, 276)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(self)

        self.horizontalLayout = QHBoxLayout()
        self.layerLabel = QLabel("Layer")
        self.horizontalLayout.addWidget(self.layerLabel)
        self.layerBox = QComboBox()
        self.horizontalLayout.addWidget(self.layerBox)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.groupBox = QGroupBox(self)
        self.verticalLayout_4 = QVBoxLayout(self.groupBox)
        self.horizontalLayout_3 = QHBoxLayout()
        self.labelWidth = QLabel(self.groupBox)
        self.horizontalLayout_3.addWidget(self.labelWidth)
        self.spinBoxWidth = QSpinBox(self.groupBox)
        self.horizontalLayout_3.addWidget(self.spinBoxWidth)
        self.labelHeight = QLabel(self.groupBox)
        self.horizontalLayout_3.addWidget(self.labelHeight)
        self.spinBoxHeight = QSpinBox(self.groupBox)
        self.horizontalLayout_3.addWidget(self.spinBoxHeight)
        self.verticalLayout_4.addLayout(self.horizontalLayout_3)
        self.verticalLayout.addWidget(self.groupBox)
        self.horizontalLayout = QHBoxLayout()
        self.groupBoxFormats = QGroupBox(self)
        self.verticalLayout_2 = QVBoxLayout(self.groupBoxFormats)
        self.checkBoxPng = QCheckBox(self.groupBoxFormats)
        self.verticalLayout_2.addWidget(self.checkBoxPng)
        self.checkBoxPng8 = QCheckBox(self.groupBoxFormats)
        self.verticalLayout_2.addWidget(self.checkBoxPng8)
        self.checkBoxJpg = QCheckBox(self.groupBoxFormats)
        self.verticalLayout_2.addWidget(self.checkBoxJpg)
        self.checkBoxGif = QCheckBox(self.groupBoxFormats)
        self.verticalLayout_2.addWidget(self.checkBoxGif)
        self.horizontalLayout.addWidget(self.groupBoxFormats)
        self.groupBoxGridsets = QGroupBox(self)
        self.verticalLayout_3 = QVBoxLayout(self.groupBoxGridsets)
        self.checkBox4326 = QCheckBox(self.groupBoxGridsets)
        self.verticalLayout_3.addWidget(self.checkBox4326)
        self.checkBox900913 = QCheckBox(self.groupBoxGridsets)
        self.verticalLayout_3.addWidget(self.checkBox900913)
        self.checkBoxGoogle = QCheckBox(self.groupBoxGridsets)
        self.verticalLayout_3.addWidget(self.checkBoxGoogle)
        self.checkBoxGlobalScale = QCheckBox(self.groupBoxGridsets)
        self.verticalLayout_3.addWidget(self.checkBoxGlobalScale)
        self.checkBoxGlobalPixel = QCheckBox(self.groupBoxGridsets)
        self.verticalLayout_3.addWidget(self.checkBoxGlobalPixel)
        self.horizontalLayout.addWidget(self.groupBoxGridsets)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self.verticalLayout.addWidget(self.buttonBox)

        self.groupBox.setTitle("Metatiling factors")
        self.labelWidth.setText("Width")
        self.labelHeight.setText("Height")
        self.groupBoxFormats.setTitle("Tile image formats")
        self.checkBoxPng.setText("png")
        self.checkBoxPng8.setText("png8")
        self.checkBoxJpg.setText("jpeg")
        self.checkBoxGif.setText("gif")
        self.groupBoxGridsets.setTitle("Gridsets")
        self.checkBox4326.setText("EPSG:4326")
        self.checkBox900913.setText("ESPG:900913")
        self.checkBoxGoogle.setText("GoogleCRS84Quad")
        self.checkBoxGlobalScale.setText("GlobalCRS84Scale")
        self.checkBoxGlobalPixel.setText("GlobalCRS84Pixel")

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def accept(self):
        self.layer = self.layers[self.layerBox.currentIndex()]
        self.metaWidth = self.spinBoxWidth.value()
        self.metaHeight = self.spinBoxHeight.value()
        checkboxes = [self.checkBox4326, self.checkBox900913, self.checkBoxGlobalPixel, self.checkBoxGlobalScale, self.checkBoxGoogle]
        self.gridsets = [checkbox.text() for checkbox in checkboxes if checkbox.isChecked()]
        checkboxes = [self.checkBoxGif, self.checkBoxJpg, self.checkBoxPng, self.checkBoxPng8]
        self.formats = ['image/' + checkbox.text() for checkbox in checkboxes if checkbox.isChecked()]
        QDialog.accept(self)

    def reject(self):
        self.layername = None
        self.formats = None
        self.gridsets = None
        self.metaWidth = None
        self.metaHeight = None
        QDialog.reject(self)


class SeedGwcLayerDialog(QDialog):

    SEED = 0
    RESEED = 1
    TRUNCATE = 2

    def __init__(self, layer, parent = None):
        super(SeedGwcLayerDialog, self).__init__(parent)
        self.layer = layer
        self.minzoom = None
        self.maxzoom = None
        self.gridset = None
        self.format = None
        self.operation = None
        self.extent = None
        self.initGui()


    def initGui(self):
        self.setWindowTitle('Seed cache layer')
        layout = QVBoxLayout()
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Close)

        horizontalLayout = QHBoxLayout()
        horizontalLayout.setSpacing(30)
        horizontalLayout.setMargin(0)
        operationLabel = QLabel('Operation')
        self.operationBox = QComboBox()
        operations = ['Seed', 'Reseed', 'Truncate']
        self.operationBox.addItems(operations)
        horizontalLayout.addWidget(operationLabel)
        horizontalLayout.addWidget(self.operationBox)
        layout.addLayout(horizontalLayout)

        horizontalLayout = QHBoxLayout()
        horizontalLayout.setSpacing(30)
        horizontalLayout.setMargin(0)
        grisetLabel = QLabel('Gridset')
        self.gridsetBox = QComboBox()
        self.gridsetBox.addItems(self.layer.gridsets)
        horizontalLayout.addWidget(grisetLabel)
        horizontalLayout.addWidget(self.gridsetBox)
        layout.addLayout(horizontalLayout)

        horizontalLayout = QHBoxLayout()
        horizontalLayout.setSpacing(30)
        horizontalLayout.setMargin(0)
        formatLabel = QLabel('Format')
        self.formatBox = QComboBox()
        self.formatBox.addItems(self.layer.mimetypes)
        horizontalLayout.addWidget(formatLabel)
        horizontalLayout.addWidget(self.formatBox)
        layout.addLayout(horizontalLayout)

        horizontalLayout = QHBoxLayout()
        horizontalLayout.setSpacing(30)
        horizontalLayout.setMargin(0)
        minZoomLabel = QLabel('Min zoom')
        self.minZoomBox = QComboBox()
        levels = [str(i) for i in range(31)]
        self.minZoomBox.addItems(levels)
        horizontalLayout.addWidget(minZoomLabel)
        horizontalLayout.addWidget(self.minZoomBox)
        layout.addLayout(horizontalLayout)

        horizontalLayout = QHBoxLayout()
        horizontalLayout.setSpacing(30)
        horizontalLayout.setMargin(0)
        maxZoomLabel = QLabel('Max zoom')
        self.maxZoomBox = QComboBox()
        levels = [str(i) for i in range(31)]
        self.maxZoomBox.addItems(levels)
        self.maxZoomBox.setCurrentIndex(15)
        horizontalLayout.addWidget(maxZoomLabel)
        horizontalLayout.addWidget(self.maxZoomBox)
        layout.addLayout(horizontalLayout)

        horizontalLayout = QHBoxLayout()
        horizontalLayout.setSpacing(30)
        horizontalLayout.setMargin(0)
        extentLabel = QLabel('Bounding box')
        self.extentPanel = ExtentSelectionPanel(self)
        horizontalLayout.addWidget(extentLabel)
        horizontalLayout.addWidget(self.extentPanel)
        layout.addLayout(horizontalLayout)

        layout.addWidget(buttonBox)
        self.setLayout(layout)

        buttonBox.accepted.connect(self.okPressed)
        buttonBox.rejected.connect(self.cancelPressed)

        self.resize(600,250)


    def okPressed(self):
        operations = ["seed", "reseed", "truncate"]
        self.minzoom = int(self.minZoomBox.currentText())
        self.maxzoom = int(self.maxZoomBox.currentText())
        self.gridset = self.gridsetBox.currentText()
        self.format = self.formatBox.currentText()
        self.operation = operations[self.operationBox.currentIndex()]
        try:
            self.extent =self.extentPanel.getValue()
        except:
            self.extentPanel.text.setStyleSheet("QLineEdit{background: yellow}")
        self.close()

    def cancelPressed(self):
        self.minzoom = None
        self.maxzoom = None
        self.gridset = None
        self.format = None
        self.operation = None
        self.extent = None
        self.close()