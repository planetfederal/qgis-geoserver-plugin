# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
"""
Contextual help components for use in dialogs, etc.
"""

import os
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *

# noinspection PyAttributeOutsideInit, PyPep8Naming
class InfoIcon(QLabel):
    def __init__(self, tip, parent=None):
        QLabel.__init__(self, parent)
        self.tiptxt = tip
        self.setSizePolicy(QSizePolicy.Fixed,
                           QSizePolicy.Fixed)
        self.setMaximumSize(QSize(16, 16))
        self.setMinimumSize(QSize(16, 16))
        infopx = QPixmap(
            os.path.dirname(os.path.dirname(__file__)) + "/images/help.png")
        self.setPixmap(infopx)

        self.setMouseTracking(True)

    def mouseMoveEvent(self, event):
        # QToolTip.showText(self.mapToGlobal(event.pos()),
        #                         self.tiptxt, self, self.rect())
        QToolTip.showText(self.mapToGlobal(event.pos()),
                                self.tiptxt, self)
        event.ignore()


# noinspection PyPep8Naming
def infoIcon(tip, parent=None):
    return InfoIcon(tip, parent)
