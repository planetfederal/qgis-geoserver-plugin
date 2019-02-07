# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
"""
Utilities to create a user-defined name for a GeoServer component, with optional
validation.
"""

from builtins import str
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *

APP = None
if __name__ == '__main__':
    import sys
    # instantiate QApplication before importing QtGui subclasses
    APP = QApplication(sys.argv)

from geoserverexplorer.gui.contextualhelp import InfoIcon


# noinspection PyPep8Naming
def xmlNameFixUp(name):
    # TODO: handle bad unicode characters, too
    n = name.replace(u' ', u'_')  # doesn't hurt to always do this
    if not xmlNameIsValid(n) and not n.startswith(u'_'):
        rx = QRegExp(r'^(?=XML|\d|\W).*', Qt.CaseInsensitive)
        if rx.exactMatch(n):
            n = u"_{0}".format(n)
    return n


# noinspection PyPep8Naming
def xmlNameRegex():
    return r'^(?!XML|\d)[_a-z]\S*'


# noinspection PyPep8Naming
def xmlNameEmptyRegex():
    return r'^(?!XML|\d)[_a-z]?(?!\W)\S*$'


# noinspection PyPep8Naming
def xmlNameIsValid(name, regex=None):
    rx = QRegExp(regex or xmlNameRegex(), Qt.CaseInsensitive)
    return rx.exactMatch(name)


# noinspection PyPep8Naming
def xmlNameRegexMsg():
    return (
        'Text must be a valid XML name:\n\n'
        '* Can contain letters, numbers, and other characters\n'
        '* Cannot start with a number or punctuation character\n'
        '* Cannot start with the letters \'xml\' (case-insensitive)\n'
        '* Cannot contain spaces'
    )


# noinspection PyAttributeOutsideInit, PyPep8Naming
class GSNameWidget(QWidget):

    nameValidityChanged = pyqtSignal(bool)  # pragma: no cover
    invalidTextChanged = pyqtSignal(str)  # pragma: no cover
    overwritingChanged = pyqtSignal(bool)  # pragma: no cover

    def __init__(self, name='', namemsg='', nameregex='', nameregexmsg='',
                 names=None, unique=False,
                 maxlength=0, allowempty=False, parent=None):
        super(GSNameWidget, self).__init__(parent)
        self.name = name
        self.namemsg = namemsg
        self.nameregex = nameregex
        self.nameregexmsg = nameregexmsg if nameregex else ''
        self.names = names if names is not None else []
        self.hasnames = len(self.names) > 0
        self.unique = self.hasnames and unique
        self.overwriting = False
        self.maxlength = maxlength if maxlength >= 0 else 0  # no negatives
        self.allowempty = allowempty
        if nameregex == xmlNameEmptyRegex():
            self.allowempty = True
        self.valid = True  # False will not trigger signal for setEnabled slots
        self.initGui()
        self.validateName()

    def initGui(self):
        layout = QHBoxLayout()
        layout.setMargin(0)
        layout.setSpacing(6)

        self.nameBox = QComboBox(self)
        self.setMinimumWidth(200)
        self.nameBox.setEditable(True)
        # add default name to choice of names, so user can select it again
        if self.name and self.name not in self.names:
            self.nameBox.addItem(self.name)
        if self.hasnames:
            self.nameBox.addItems(self.names)
        self.nameBox.setCurrentIndex(-1)

        self.nameBox.lineEdit().setText(self.name)
        self.nameBox.lineEdit().textChanged.connect(self.validateName)
        self.nameValidityChanged.connect(self.highlightName)
        self.invalidTextChanged.connect(self.showInvalidToolTip)
        phtxt = "Optional" if self.allowempty else "Required"
        self.nameBox.lineEdit().setPlaceholderText(phtxt)
        layout.addWidget(self.nameBox)

        tip = 'Define a{0}{1} name'.format(' valid' if self.nameregex else '',
                                           ' unique' if self.unique else '')
        if self.maxlength > 0:
            tip += ' <= {0} characters'.format(self.maxlength)
        if self.hasnames and not self.unique:
            tip += ' or choose from existing'

        if self.namemsg:
            if tip:
                tip += '\n\n'
            tip += self.namemsg

        if self.nameregexmsg:
            if tip:
                tip += '\n\n'
            tip += self.nameregexmsg

        if self.namemsg or self.nameregex or self.nameregexmsg or self.hasnames:
            infolabel = InfoIcon(tip, self)
            layout.addWidget(infolabel)

        self.setLayout(layout)

    def isValid(self):
        return self.valid

    def definedName(self):
        return str(self.nameBox.lineEdit().text()) if self.valid else None

    def overwritingName(self):
        return self.overwriting

    @pyqtSlot(str)
    def showInvalidToolTip(self, txt):
        bxpos = self.nameBox.pos()
        QTimer.singleShot(250, lambda:
        QToolTip.showText(
            self.mapToGlobal(
                QPoint(bxpos.x(),
                              bxpos.y() + self.nameBox.height()/2)),
            txt,
            self.nameBox) if self.nameBox else None)

    @pyqtSlot(str)
    def setName(self, txt):
        self.name = txt
        self.nameBox.lineEdit().setText(txt)

    @pyqtSlot(list)
    def setNames(self, names):
        curname = self.nameBox.currentText()
        self.names = names

        self.blockSignals(True)
        self.nameBox.clear()
        if self.name and self.name not in self.names:
            self.nameBox.addItem(self.name)
        if len(names) > 0:
            self.nameBox.addItems(names)
        self.blockSignals(False)

        if curname != self.nameBox.currentText():
            self.setName(curname)  # validates
        else:
            self.validateName()

    @pyqtSlot(str, str)
    def setNameRegex(self, regex, regexmsg):
        self.nameregex = regex
        self.nameregexmsg = regexmsg
        if regex == xmlNameEmptyRegex():
            self.allowempty = True
        self.validateName()

    @pyqtSlot(int)
    def setMaxLength(self, num):
        self.maxlength = num
        self.validateName()

    @pyqtSlot(bool)
    def setAllowEmpty(self, empty):
        self.allowempty = empty
        self.validateName()

    @pyqtSlot(bool)
    def setUnique(self, unique):
        self.unique = self.hasnames and unique
        self.validateName()

    @pyqtSlot()
    def validateName(self, name=None):
        if name is None:
            name = self.nameBox.lineEdit().text()
        curvalid = self.valid

        invalidtxt = "Name can not be empty"
        valid = True if self.allowempty else len(name) > 0

        # check if character limit reached
        if valid and self.maxlength > 0:
            invalidtxt = "Name length can not be > {0}".format(self.maxlength)
            valid = len(name) <= self.maxlength

        # validate regex, if defined
        if valid and self.nameregex:
            rx = QRegExp(self.nameregex, Qt.CaseInsensitive)
            invalidtxt = "Name doesn't match expression {0}"\
                .format(self.nameregex)
            valid = rx.exactMatch(name)

        if valid:
            overwriting = False
            if self.unique:  # crosscheck for unique name
                invalidtxt = "Name is not unique"
                valid = name not in self.names
            else:  # crosscheck for overwrite
                overwriting = name in self.names
            self.overwriting = overwriting
            self.overwritingChanged.emit(overwriting)

        if curvalid != valid:
            self.valid = valid
            self.nameValidityChanged.emit(valid)

        self.nameBox.setToolTip(invalidtxt if not valid else '')
        if not valid:
            self.invalidTextChanged.emit(invalidtxt)

    @pyqtSlot()
    def highlightName(self):
        self.nameBox.lineEdit().setStyleSheet(
            '' if self.valid else 'QLineEdit {color: rgb(200, 0, 0)}')


if __name__ == '__main__':
    # noinspection PyPep8Naming
    class BounceObj(QObject):

        @pyqtSlot(bool)
        def valididtyChanged(self, valid):
            # fix_print_with_import
            print("valididty changed: {0}".format(valid))

        @pyqtSlot(bool)
        def overwritingChanged(self, overwrite):
            # fix_print_with_import
            print("overwriting changed: {0}".format(overwrite))

    bobj = BounceObj()
    gdlg = GSNameWidget(
        namemsg='Sample is generated from PostgreSQL connection name',
        name=xmlNameFixUp('My PG connection'),
        nameregex=xmlNameRegex(),
        nameregexmsg=xmlNameRegexMsg(),
        names=['name_one', 'name_two'],
        unique=False,
        maxlength=10)
    gdlg.nameValidityChanged.connect(bobj.valididtyChanged)
    gdlg.overwritingChanged.connect(bobj.overwritingChanged)
    gdlg.show()
    gdlg.raise_()
    gdlg.activateWindow()
    sys.exit(APP.exec_())


def isNameValid(name, names, maxlength=0, nameregex=''):
        # no zero char names allowed
        valid = len(name) > 0

        # check if character limit reached
        if valid and maxlength > 0:
            valid = len(name) <= maxlength

        # validate regex, if defined
        if valid and nameregex:
            rx = QRegExp(nameregex, 0)
            valid = rx.exactMatch(name)

        return valid

if __name__ == '__main__':
    # noinspection PyPep8Naming
    class BounceObj(QObject):

        @pyqtSlot(bool)
        def valididtyChanged(self, valid):
            # fix_print_with_import
            print("valididty changed: {0}".format(valid))

        @pyqtSlot(bool)
        def overwritingChanged(self, overwrite):
            # fix_print_with_import
            print("overwriting changed: {0}".format(overwrite))

    bobj = BounceObj()
    gdlg = GSNameWidget(
        namemsg='Sample is generated from PostgreSQL connection name',
        name=xmlNameFixUp('My PG connection'),
        nameregex=xmlNameRegex(),
        nameregexmsg=xmlNameRegexMsg(),
        names=['name_one', 'name_two'],
        unique=False,
        maxlength=10)
    gdlg.nameValidityChanged.connect(bobj.valididtyChanged)
    gdlg.overwritingChanged.connect(bobj.overwritingChanged)
    gdlg.show()
    gdlg.raise_()
    gdlg.activateWindow()
    sys.exit(APP.exec_())
