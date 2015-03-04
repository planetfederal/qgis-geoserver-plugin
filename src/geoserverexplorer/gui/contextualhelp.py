"""
Contextual help components for use in dialogs, etc.
"""

import os
from PyQt4 import QtGui, QtCore


# noinspection PyAttributeOutsideInit, PyPep8Naming
class InfoIcon(QtGui.QLabel):
    def __init__(self, tip, parent=None):
        QtGui.QLabel.__init__(self, parent)
        self.tiptxt = tip
        self.setSizePolicy(QtGui.QSizePolicy.Fixed,
                           QtGui.QSizePolicy.Fixed)
        self.setMaximumSize(QtCore.QSize(16, 16))
        self.setMinimumSize(QtCore.QSize(16, 16))
        infopx = QtGui.QPixmap(
            os.path.dirname(os.path.dirname(__file__)) + "/images/help.png")
        self.setPixmap(infopx)

        self.setMouseTracking(True)

    def mouseMoveEvent(self, event):
        # QtGui.QToolTip.showText(self.mapToGlobal(event.pos()),
        #                         self.tiptxt, self, self.rect())
        QtGui.QToolTip.showText(self.mapToGlobal(event.pos()),
                                self.tiptxt, self)
        event.ignore()


# noinspection PyPep8Naming
def infoIcon(tip, parent=None):
    return InfoIcon(tip, parent)
