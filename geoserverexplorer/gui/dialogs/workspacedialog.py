# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
from builtins import str
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *

APP = None
if __name__ == '__main__':
    import sys
    # instantiate QApplication before importing QtGui subclasses
    APP = QApplication(sys.argv)

from geoserverexplorer.gui.gsnameutils import GSNameWidget, xmlNameRegexMsg, xmlNameRegex


class DefineWorkspaceDialog(QDialog):

    def __init__(self, workspaces=None, parent=None):
        super(DefineWorkspaceDialog, self).__init__(parent)
        self.workspaces = workspaces if workspaces is not None else []
        self.uri = None
        self.name = None
        self.initGui()


    def initGui(self):
        self.setWindowTitle('New workspace')
        verticalLayout = QVBoxLayout()

        horizontalLayout = QHBoxLayout()
        horizontalLayout.setSpacing(30)
        horizontalLayout.setMargin(0)
        nameLabel = QLabel('Workspace name')
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

        horizontalLayout = QHBoxLayout()
        horizontalLayout.setSpacing(30)
        horizontalLayout.setMargin(0)
        uriLabel = QLabel('URI')
        uriLabel.setMinimumWidth(150)
        self.uriBox = QLineEdit()
        self.uriBox.setText('')
        self.uriBox.setPlaceholderText('Required')
        self.uriBox.setMinimumWidth(250)
        horizontalLayout.addWidget(uriLabel)
        horizontalLayout.addWidget(self.uriBox)
        verticalLayout.addLayout(horizontalLayout)

        self.groupBox = QGroupBox()
        self.groupBox.setLayout(verticalLayout)

        layout = QVBoxLayout()
        layout.addWidget(self.groupBox)
        self.spacer = QSpacerItem(20,20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(self.spacer)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.okButton = self.buttonBox.button(QDialogButtonBox.Ok)
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
        self.uri = str(self.uriBox.text())
        self.name = str(self.nameBox.definedName())
        self.close()

    def cancelPressed(self):
        self.uri = None
        self.name = None
        self.close()

if __name__ == '__main__':
    wsdlg = DefineWorkspaceDialog(workspaces=['ws_one', 'ws_two'])
    wsdlg.exec_()
