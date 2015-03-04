from geoserverexplorer.gui.extentpanel import ExtentSelectionPanel
from PyQt4 import QtGui, QtCore

class EditGwcLayerDialog(QtGui.QDialog):

    def __init__(self, layers, gwclayer = None):
        QtGui.QDialog.__init__(self)
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
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.verticalLayout = QtGui.QVBoxLayout(self)

        self.horizontalLayout = QtGui.QHBoxLayout()
        self.layerLabel = QtGui.QLabel("Layer")
        self.horizontalLayout.addWidget(self.layerLabel)
        self.layerBox = QtGui.QComboBox()
        self.horizontalLayout.addWidget(self.layerBox)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.groupBox = QtGui.QGroupBox(self)
        self.verticalLayout_4 = QtGui.QVBoxLayout(self.groupBox)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.labelWidth = QtGui.QLabel(self.groupBox)
        self.horizontalLayout_3.addWidget(self.labelWidth)
        self.spinBoxWidth = QtGui.QSpinBox(self.groupBox)
        self.horizontalLayout_3.addWidget(self.spinBoxWidth)
        self.labelHeight = QtGui.QLabel(self.groupBox)
        self.horizontalLayout_3.addWidget(self.labelHeight)
        self.spinBoxHeight = QtGui.QSpinBox(self.groupBox)
        self.horizontalLayout_3.addWidget(self.spinBoxHeight)
        self.verticalLayout_4.addLayout(self.horizontalLayout_3)
        self.verticalLayout.addWidget(self.groupBox)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.groupBoxFormats = QtGui.QGroupBox(self)
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.groupBoxFormats)
        self.checkBoxPng = QtGui.QCheckBox(self.groupBoxFormats)
        self.verticalLayout_2.addWidget(self.checkBoxPng)
        self.checkBoxPng8 = QtGui.QCheckBox(self.groupBoxFormats)
        self.verticalLayout_2.addWidget(self.checkBoxPng8)
        self.checkBoxJpg = QtGui.QCheckBox(self.groupBoxFormats)
        self.verticalLayout_2.addWidget(self.checkBoxJpg)
        self.checkBoxGif = QtGui.QCheckBox(self.groupBoxFormats)
        self.verticalLayout_2.addWidget(self.checkBoxGif)
        self.horizontalLayout.addWidget(self.groupBoxFormats)
        self.groupBoxGridsets = QtGui.QGroupBox(self)
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.groupBoxGridsets)
        self.checkBox4326 = QtGui.QCheckBox(self.groupBoxGridsets)
        self.verticalLayout_3.addWidget(self.checkBox4326)
        self.checkBox900913 = QtGui.QCheckBox(self.groupBoxGridsets)
        self.verticalLayout_3.addWidget(self.checkBox900913)
        self.checkBoxGoogle = QtGui.QCheckBox(self.groupBoxGridsets)
        self.verticalLayout_3.addWidget(self.checkBoxGoogle)
        self.checkBoxGlobalScale = QtGui.QCheckBox(self.groupBoxGridsets)
        self.verticalLayout_3.addWidget(self.checkBoxGlobalScale)
        self.checkBoxGlobalPixel = QtGui.QCheckBox(self.groupBoxGridsets)
        self.verticalLayout_3.addWidget(self.checkBoxGlobalPixel)
        self.horizontalLayout.addWidget(self.groupBoxGridsets)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.verticalLayout.addWidget(self.buttonBox)

        self.groupBox.setTitle("Metatiling factors")
        self.labelWidth.setText("Width")
        self.labelHeight.setText("Height")
        self.groupBoxFormats.setTitle("Tile image formats")
        self.checkBoxPng.setText("png")
        self.checkBoxPng8.setText("png8")
        self.checkBoxJpg.setText("jpg")
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
        QtGui.QDialog.accept(self)

    def reject(self):
        self.layername = None
        self.formats = None
        self.gridsets = None
        self.metaWidth = None
        self.metaHeight = None
        QtGui.QDialog.reject(self)


class SeedGwcLayerDialog(QtGui.QDialog):

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
        layout = QtGui.QVBoxLayout()
        buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Close)

        horizontalLayout = QtGui.QHBoxLayout()
        horizontalLayout.setSpacing(30)
        horizontalLayout.setMargin(0)
        operationLabel = QtGui.QLabel('Operation')
        self.operationBox = QtGui.QComboBox()
        operations = ['Seed', 'Reseed', 'Truncate']
        self.operationBox.addItems(operations)
        horizontalLayout.addWidget(operationLabel)
        horizontalLayout.addWidget(self.operationBox)
        layout.addLayout(horizontalLayout)

        horizontalLayout = QtGui.QHBoxLayout()
        horizontalLayout.setSpacing(30)
        horizontalLayout.setMargin(0)
        grisetLabel = QtGui.QLabel('Gridset')
        self.gridsetBox = QtGui.QComboBox()
        self.gridsetBox.addItems(self.layer.gridsets)
        horizontalLayout.addWidget(grisetLabel)
        horizontalLayout.addWidget(self.gridsetBox)
        layout.addLayout(horizontalLayout)

        horizontalLayout = QtGui.QHBoxLayout()
        horizontalLayout.setSpacing(30)
        horizontalLayout.setMargin(0)
        formatLabel = QtGui.QLabel('Format')
        self.formatBox = QtGui.QComboBox()
        self.formatBox.addItems(self.layer.mimetypes)
        horizontalLayout.addWidget(formatLabel)
        horizontalLayout.addWidget(self.formatBox)
        layout.addLayout(horizontalLayout)

        horizontalLayout = QtGui.QHBoxLayout()
        horizontalLayout.setSpacing(30)
        horizontalLayout.setMargin(0)
        minZoomLabel = QtGui.QLabel('Min zoom')
        self.minZoomBox = QtGui.QComboBox()
        levels = [str(i) for i in range(31)]
        self.minZoomBox.addItems(levels)
        horizontalLayout.addWidget(minZoomLabel)
        horizontalLayout.addWidget(self.minZoomBox)
        layout.addLayout(horizontalLayout)

        horizontalLayout = QtGui.QHBoxLayout()
        horizontalLayout.setSpacing(30)
        horizontalLayout.setMargin(0)
        maxZoomLabel = QtGui.QLabel('Max zoom')
        self.maxZoomBox = QtGui.QComboBox()
        levels = [str(i) for i in range(31)]
        self.maxZoomBox.addItems(levels)
        self.maxZoomBox.setCurrentIndex(15)
        horizontalLayout.addWidget(maxZoomLabel)
        horizontalLayout.addWidget(self.maxZoomBox)
        layout.addLayout(horizontalLayout)

        horizontalLayout = QtGui.QHBoxLayout()
        horizontalLayout.setSpacing(30)
        horizontalLayout.setMargin(0)
        extentLabel = QtGui.QLabel('Bounding box')
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