# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
import os
import webbrowser
import config
from geoserverexplorer.gui.explorer import GeoServerExplorer
from geoserverexplorer.gui.dialogs.configdialog import ConfigDialog
from geoserverexplorer.geoserver import pem
from PyQt4 import QtGui, QtCore
try:
    from processing.core.Processing import Processing
    from processingprovider.geoserverprovider import GeoServerProvider
    processingOk = True
except:
    processingOk = False
from geoserverexplorer.qgis.sldadapter import adaptGsToQgs
from geoserverexplorer.qgis import layerwatcher


class GeoServerExplorerPlugin:

    def __init__(self, iface):
        self.iface = iface
        config.iface = iface
        if processingOk:
            self.provider = GeoServerProvider()

        try:
            from qgistester.tests import addTestModule
            from geoserverexplorer.test import testplugin
            from geoserverexplorer.test import testpkiplugin
            addTestModule(testplugin, "GeoServer")
            addTestModule(testpkiplugin, "PKI GeoServer")
        except Exception as ex:
            pass

    def unload(self):
        pem.removePkiTempFiles(self.explorer.catalogs())
        self.explorer.deleteLater()
        self.iface.removePluginWebMenu(u"GeoServer", self.explorerAction)
        self.iface.removePluginWebMenu(u"GeoServer", self.configAction)
        self.iface.removePluginWebMenu(u"GeoServer", self.helpAction)
        if processingOk:
            Processing.removeProvider(self.provider)
        layerwatcher.disconnectLayerWasAdded()
        try:
            from qgistester.tests import removeTestModule
            from geoserverexplorer.test import testplugin
            from geoserverexplorer.test import testpkiplugin
            removeTestModule(testplugin, "GeoServer")
            removeTestModule(testpkiplugin, "PKI GeoServer")
        except Exception as ex:
            pass

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

        if processingOk:
            Processing.addProvider(self.provider)

        layerwatcher.connectLayerWasAdded(self.explorer)


    def _explorerVisibilityChanged(self, visible):
        settings = QtCore.QSettings()
        settings.setValue("/GeoServer/Settings/General/ExplorerVisible", visible)

    def showHelp(self):
        HELP_URL = "https://github.com/boundlessgeo/qgis-geoserver-plugin/blob/master/docs/source/intro.rst"
        webbrowser.open(HELP_URL)

    def openExplorer(self):
        self.explorer.show()

    def openSettings(self):
        dlg = ConfigDialog(self.explorer)
        dlg.exec_()
