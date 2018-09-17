# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
from builtins import str
import os
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *
import sip
from qgis.core import *
from qgis.gui import *
from qgis.utils import iface
from geoserverexplorer.geoserver import GeoserverException
from geoserverexplorer.gui.exploreritems import *
import traceback
from geoserverexplorer.gui.explorertree import ExplorerTreeWidget
from geoserverexplorer.qgis.utils import UserCanceledOperation
from qgiscommons2.settings import pluginSetting
from geoserver.catalog import FailedRequestError
from geoserverexplorer.gui import setInfo, setWarning, setError

class GeoServerExplorer(QDockWidget):

    def __init__(self, parent = None):
        super(GeoServerExplorer, self).__init__(parent)
        self.setObjectName('GeoServerExplorer')
        self.initGui()

    def initGui(self):
        self.progressMaximum = 0
        self.isProgressVisible = False
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.dockWidgetContents = QWidget()
        self.setWindowTitle('GeoServer Explorer')
        self.splitter = QSplitter()
        self.splitter.setOrientation(Qt.Vertical)
        self.subwidget = QWidget()
        self.explorerTree = self.tree = ExplorerTreeWidget(self)
        showToolbar = pluginSetting("ShowToolbar")
        self.toolbar = QToolBar()
        self.toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.toolbar.setVisible(showToolbar)
        self.setToolbarActions([])
        self.splitter.addWidget(self.explorerTree)
        self.log = QTextEdit()
        self.description = QWidget()
        self.descriptionLayout = QVBoxLayout()
        self.descriptionLayout.setSpacing(2)
        self.descriptionLayout.setMargin(0)
        self.description.setLayout(self.descriptionLayout)
        self.splitter.addWidget(self.description)
        self.setDescriptionWidget()
        showDescription = pluginSetting("ShowDescription")
        self.description.setVisible(showDescription)
        self.progress = None
        self.layout = QVBoxLayout()
        self.layout.setSpacing(2)
        self.layout.setMargin(0)
        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.splitter)
        self.dockWidgetContents.setLayout(self.layout)
        self.setWidget(self.dockWidgetContents)

        self.topLevelChanged.connect(self.dockStateChanged)

    def dockStateChanged(self, floating):
        if floating:
            self.resize(800, 450)
            self.splitter.setOrientation(Qt.Horizontal)
        else:
            self.splitter.setOrientation(Qt.Vertical)

    def setToolbarActions(self, actions):
        self.toolbar.clear()
        for action in actions:
            if action.icon().isNull():
                icon = QIcon(os.path.dirname(__file__) + "/../images/process.png")
                action.setIcon(icon)

        for action in actions:
            button = QPushButton()
            button.setIcon(action.icon())
            button.setToolTip(action.text())
            button.setEnabled(action.isEnabled())
            button.clicked.connect(action.trigger)
            self.toolbar.addWidget(button)

        self.toolbar.update()

    def refreshContent(self):
        showDescription = pluginSetting("ShowDescription")
        self.description.setVisible(showDescription)
        showToolbar = pluginSetting("ShowToolbar")
        self.toolbar.setVisible(showToolbar)
        self.refreshDescription()

    def catalogs(self):
        if self.explorerTree is None:
            return {}
        return self.explorerTree.gsItem._catalogs

    def run(self, command, msg, refresh, *params):
        noerror = True
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        try:
            command(*params)
            for item in refresh:
                if item is not None:
                    item.refreshContent(self)
            if None in refresh:
                self.refreshContent()
            if msg is not None and not self.isProgressVisible:
                setInfo("Operation <i>" + msg + "</i> correctly executed")
        except UserCanceledOperation:
            pass
        except Exception as e:
            if isinstance(e, FailedRequestError):
                setError("Error connecting to server (See log for more details)", traceback.format_exc())
            elif isinstance(e, GeoserverException):
                setError(str(e), e.details)
            else:
                setError(str(e) + " (See log for more details)", traceback.format_exc())
            noerror = False
        finally:
            QApplication.restoreOverrideCursor()
            self.refreshDescription()

        return noerror

    def resetActivity(self):
        if self.progress is not None:
            iface.messageBar().clearWidgets()
            self.isProgressVisible = False
            self.progress = None
            self.progressMaximum = 0

    def setProgress(self, value):
        if self.progress is not None and not sip.isdeleted(self.progress):
            self.progress.setValue(value)

    def setProgressMaximum(self, value, msg = ""):
        self.progressMaximum = value
        self.isProgressVisible = True
        self.progressMessageBar = iface.messageBar().createMessage(msg)
        self.progress = QProgressBar()
        self.progress.setMaximum(self.progressMaximum)
        self.progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.progressMessageBar.layout().addWidget(self.progress)
        iface.messageBar().pushWidget(self.progressMessageBar, Qgis.Info)

    def setDescriptionWidget(self, widget = None):
        item = self.descriptionLayout.itemAt(0)
        if item:
            self.descriptionLayout.removeItem(item)
            item.widget().close()
        if widget is None:
            widget = QTextBrowser()
            widget.setHtml(u'<div style="background-color:#C7DBFC; color:#555555"><h1>Select an item above for contextual description</h1></div><ul>')

        self.descriptionLayout.addWidget(widget)

    def refreshDescription(self):
        item = self.explorerTree.lastClickedItem()
        if item is not None:
            try:
                self.explorerTree.treeItemClicked(item, 0)
            except:
                self.setDescriptionWidget(None)
