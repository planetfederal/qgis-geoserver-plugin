# -*- coding: utf-8 -*-

import os
import webbrowser
import config
from geoserverexplorer.gui.explorer import GeoServerExplorer
from geoserverexplorer.gui.dialogs.configdialog import ConfigDialog
from geoserverexplorer.geoserver import pem
from PyQt4 import QtGui, QtCore
from processing.core.Processing import Processing
from processingprovider.geoserverprovider import GeoServerProvider

class GeoServerExplorerPlugin:

    def __init__(self, iface):
        self.iface = iface
        config.iface = iface
        self.provider = GeoServerProvider()

    def unload(self):
        pem.removePkiTempFiles(self.explorer.catalogs())
        self.explorer.deleteLater()
        self.iface.removePluginWebMenu(u"GeoServer", self.explorerAction)
        self.iface.removePluginWebMenu(u"GeoServer", self.configAction)
        self.iface.removePluginWebMenu(u"GeoServer", self.helpAction)
        Processing.removeProvider(self.provider)

    def initGui(self):
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/images/geoserver.png")
        self.explorerAction = QtGui.QAction(icon, "GeoServer Explorer", self.iface.mainWindow())
        self.explorerAction.triggered.connect(self.openExplorer)
        self.iface.addPluginToWebMenu(u"GeoServer", self.explorerAction)

        settings = QtCore.QSettings()
        self.explorer = GeoServerExplorer()
        self.iface.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.explorer)
        if not settings.value("/GeoServer/Settings/General/ExplorerVisible", False, bool):
            self.explorer.hide()
        self.explorer.visibilityChanged.connect(self._explorerVisibilityChanged)


        icon = QtGui.QIcon(os.path.dirname(__file__) + "/images/config.png")
        self.configAction = QtGui.QAction(icon, "GeoServer Explorer settings", self.iface.mainWindow())
        self.configAction.triggered.connect(self.openSettings)
        self.iface.addPluginToWebMenu(u"GeoServer", self.configAction)

        icon = QtGui.QIcon(os.path.dirname(__file__) + "/images/help.png")
        self.helpAction = QtGui.QAction(icon, "GeoServer Explorer help", self.iface.mainWindow())
        self.helpAction.triggered.connect(self.showHelp)
        self.iface.addPluginToWebMenu(u"GeoServer", self.helpAction)

        Processing.addProvider(self.provider)

    def _explorerVisibilityChanged(self, visible):
        settings = QtCore.QSettings()
        settings.setValue("/GeoServer/Settings/General/ExplorerVisible", visible)

    def showHelp(self):
        HELP_URL = "https://github.com/boundlessgeo/qgis-geoserver-plugin/blob/master/doc/source/intro.rst"
        webbrowser.open(HELP_URL)

    def openExplorer(self):
        self.explorer.show()

    def openSettings(self):
        dlg = ConfigDialog(self.explorer)
        dlg.exec_()
