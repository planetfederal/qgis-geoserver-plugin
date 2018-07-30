# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
"""
Dialog to create a user-defined name for a GeoServer component, with optional
validation.
"""

from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *

APP = None
if __name__ == '__main__':
    import sys
    # instantiate QApplication before importing QtGui subclasses
    APP = QApplication(sys.argv)

from geoserverexplorer.gui.gsnameutils import GSNameWidget
from geoserverexplorer.qgis.utils import UserCanceledOperation
from geoserverexplorer.gui.gsnameutils import GSNameWidget, \
    xmlNameFixUp, xmlNameRegex, xmlNameRegexMsg


# noinspection PyAttributeOutsideInit, PyPep8Naming
class GSNameDialog(QDialog):

    def __init__(self, boxtitle='', boxmsg='', name='', namemsg='',
                 nameregex='', nameregexmsg='', names=None,
                 unique=False, maxlength=0, parent=None):
        super(GSNameDialog, self).__init__(parent)
        self.boxtitle = boxtitle
        self.boxmsg = boxmsg
        self.nameBox = GSNameWidget(
            name=name,
            namemsg=namemsg,
            nameregex=nameregex,
            nameregexmsg=nameregexmsg,
            names=names,
            unique=unique,
            maxlength=maxlength
        )
        self.initGui()

    def initGui(self):
        self.setWindowTitle('Define name')
        vertlayout = QVBoxLayout()

        self.groupBox = QGroupBox()
        self.groupBox.setTitle(self.boxtitle)
        self.groupBox.setLayout(vertlayout)

        if self.boxmsg:
            self.groupBoxMsg = QLabel(self.boxmsg)
            self.groupBoxMsg.setWordWrap(True)
            self.groupBox.layout().addWidget(self.groupBoxMsg)

        self.groupBox.layout().addWidget(self.nameBox)

        layout = QVBoxLayout()
        layout.addWidget(self.groupBox)
        self.buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.okButton = self.buttonBox.button(QDialogButtonBox.Ok)
        self.cancelButton = self.buttonBox.button(QDialogButtonBox.Cancel)
        layout.addWidget(self.buttonBox)

        self.setLayout(layout)

        self.nameBox.nameValidityChanged.connect(self.okButton.setEnabled)
        self.nameBox.overwritingChanged.connect(self.updateButtons)

        # noinspection PyUnresolvedReferences
        self.buttonBox.accepted.connect(self.accept)
        # noinspection PyUnresolvedReferences
        self.buttonBox.rejected.connect(self.reject)

        self.setMinimumWidth(240)

        # respond to intial validation
        self.okButton.setEnabled(self.nameBox.isValid())
        self.updateButtons(self.nameBox.overwritingName())

    def definedName(self):
        return self.nameBox.definedName()

    def overwritingName(self):
        return self.nameBox.overwritingName()

    @pyqtSlot(bool)
    def updateButtons(self, overwriting):
        txt = "Overwrite" if overwriting else "OK"
        self.okButton.setText(txt)
        self.okButton.setDefault(not overwriting)
        self.cancelButton.setDefault(overwriting)


class GSXmlNameDialog(GSNameDialog):

    def __init__(self, kind, **kwargs):
        unique = kwargs.get('unique', False)
        super(GSXmlNameDialog, self).__init__(
            boxtitle='GeoServer {0} name'.format(kind),
            boxmsg='Define unique {0}'.format(kind) +
                   ' or overwrite existing' if not unique else '',
            name=xmlNameFixUp(kwargs.get('name', '')),
            namemsg=kwargs.get('namemsg', ''),
            nameregex=kwargs.get('nameregex', xmlNameRegex()),
            nameregexmsg=kwargs.get('nameregexmsg', xmlNameRegexMsg()),
            names=kwargs.get('names', None),
            unique=unique,
            maxlength=kwargs.get('maxlength', 0),
            parent=kwargs.get('parent', None))


def getGSXmlName(kind, **kwargs):
    dlg = GSXmlNameDialog(kind=kind, **kwargs)
    QApplication.setOverrideCursor(QCursor(Qt.ArrowCursor))
    res = dlg.exec_()
    QApplication.restoreOverrideCursor()
    if res:
        return dlg.definedName()
    else:
        raise UserCanceledOperation()


def getGSLayerName(**kwargs):
    return getGSXmlName('layer', **kwargs)


def getGSStoreName(**kwargs):
    return getGSXmlName('data store', **kwargs)


if __name__ == '__main__':
    from geoserverexplorer.gui.gsnameutils import \
        xmlNameFixUp, xmlNameRegex, xmlNameRegexMsg
    gdlg = GSNameDialog(
        boxtitle='GeoServer data store name',
        boxmsg='My groupbox message',
        namemsg='Sample is generated from PostgreSQL connection name.',
        # name=xmlNameFixUp('My PG connection'),
        name='name_one',
        nameregex=xmlNameRegex(),
        nameregexmsg=xmlNameRegexMsg(),
        names=['name_one', 'name_two'],
        unique=False,
        maxlength=10)
    gdlg.exec_()
    # fix_print_with_import
    print(gdlg.definedName())
    # fix_print_with_import
    print(gdlg.overwritingName())
    # and with no kwargs
    gdlg = GSNameDialog()
    gdlg.exec_()
    # fix_print_with_import
    print(gdlg.definedName())
    # fix_print_with_import
    print(gdlg.overwritingName())
    # gdlg.show()
    # gdlg.raise_()
    # gdlg.activateWindow()
    # sys.exit(APP.exec_())
