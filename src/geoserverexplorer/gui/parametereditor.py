from PyQt4 import QtCore, QtGui

class ParameterEditor(QtGui.QWidget):
    def __init__(self, settings, explorer):
        self.explorer = explorer
        self.settings = settings
        self.parameters = settings.settings()
        QtGui.QWidget.__init__(self)
        self.setupUi()

    def setupUi(self):
        layout = QtGui.QVBoxLayout()
        layout.setSpacing(2)
        layout.setMargin(0)
        self.tree = QtGui.QTreeWidget()
        self.tree.setAlternatingRowColors(True)
        self.tree.headerItem().setText(0, "Setting")
        self.tree.headerItem().setText(1, "Value")
        self.tree.setColumnWidth(0, 150)
        layout.addWidget(self.tree)
        for section in self.parameters:
            params = self.parameters[section]
            paramsItem = QtGui.QTreeWidgetItem()
            paramsItem.setText(0, section)
            for name, value in params:
                item = QtGui.QTreeWidgetItem()
                item.setText(0, name)
                item.setText(1, value)
                item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
                paramsItem.addChild(item)
            self.tree.addTopLevelItem(paramsItem)
        button = QtGui.QPushButton()
        button.setText("Save")
        button.clicked.connect(self.saveSettings)
        buttonBox = QtGui.QDialogButtonBox()
        buttonBox.setOrientation(QtCore.Qt.Horizontal)
        buttonBox.addButton(button, QtGui.QDialogButtonBox.ActionRole)
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


