# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
from PyQt4 import QtGui

APP = None
if __name__ == '__main__':
    import sys
    # instantiate QApplication before importing QtGui subclasses
    APP = QtGui.QApplication(sys.argv)

from geoserverexplorer.gui.gsnameutils import GSNameWidget, xmlNameRegexMsg, xmlNameRegex


class DefineWorkspaceDialog(QtGui.QDialog):

    def __init__(self, workspaces=None, parent=None):
        super(DefineWorkspaceDialog, self).__init__(parent)
        self.workspaces = workspaces if workspaces is not None else []
        self.uri = None
        self.name = None
        self.initGui()


    def initGui(self):
        self.setWindowTitle('New workspace')
        verticalLayout = QtGui.QVBoxLayout()

        horizontalLayout = QtGui.QHBoxLayout()
        horizontalLayout.setSpacing(30)
        horizontalLayout.setMargin(0)
        nameLabel = QtGui.QLabel('Workspace name')
        nameLabel.setMinimumWidth(150)
        self.nameBox = GSNameWidget(
            namemsg='',
            name='workspace',
            nameregex=xmlNameRegex(),
            nameregexmsg=xmlNameRegexMsg(),
            names=self.workspaces,
            unique=True,
            maxlength=10)
        self.nameBox.setMinimumWidth(250)
        horizontalLayout.addWidget(nameLabel)
        horizontalLayout.addWidget(self.nameBox)
        verticalLayout.addLayout(horizontalLayout)

        horizontalLayout = QtGui.QHBoxLayout()
        horizontalLayout.setSpacing(30)
        horizontalLayout.setMargin(0)
        uriLabel = QtGui.QLabel('URI')
        uriLabel.setMinimumWidth(150)
        self.uriBox = QtGui.QLineEdit()
        self.uriBox.setText('')
        self.uriBox.setPlaceholderText('Required')
        self.uriBox.setMinimumWidth(250)
        horizontalLayout.addWidget(uriLabel)
        horizontalLayout.addWidget(self.uriBox)
        verticalLayout.addLayout(horizontalLayout)

        self.groupBox = QtGui.QGroupBox()
        self.groupBox.setLayout(verticalLayout)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.groupBox)
        self.spacer = QtGui.QSpacerItem(20,20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        layout.addItem(self.spacer)

        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        self.okButton = self.buttonBox.button(QtGui.QDialogButtonBox.Ok)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)

        self.buttonBox.accepted.connect(self.okPressed)
        self.buttonBox.rejected.connect(self.cancelPressed)

        self.nameBox.nameValidityChanged.connect(self.updateOkButton)
        self.uriBox.textChanged.connect(self.updateOkButton)
        self.updateOkButton()

    def getWorkspace(self):
        return self.workspace

    def updateOkButton(self):
        ok = self.nameBox.isValid() and self.uriBox.text() != ''
        self.okButton.setEnabled(ok)

    def okPressed(self):
        self.uri = unicode(self.uriBox.text())
        self.name = unicode(self.nameBox.definedName())
        self.close()

    def cancelPressed(self):
        self.uri = None
        self.name = None
        self.close()

if __name__ == '__main__':
    wsdlg = DefineWorkspaceDialog(workspaces=['ws_one', 'ws_two'])
    wsdlg.exec_()
