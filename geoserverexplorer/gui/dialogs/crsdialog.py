# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
from qgis.core import *
from qgis.gui import *
from PyQt4 import QtGui

class CrsSelectionDialog(QtGui.QDialog):

    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.authid = None
        layout = QtGui.QVBoxLayout()
        self.selector = QgsProjectionSelector(self)
        buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Close)
        layout.addWidget(self.selector)
        layout.addWidget(buttonBox)
        self.setLayout(layout)

        buttonBox.accepted.connect(self.okPressed)
        buttonBox.rejected.connect(self.cancelPressed)

    def okPressed(self):
        self.authid = self.selector.selectedAuthId()
        self.close()

    def cancelPressed(self):
        self.authid = None
        self.close()
