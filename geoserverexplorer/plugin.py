# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
import os
import config
from geoserverexplorer.gui.explorer import GeoServerExplorer
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
from qgiscommons.settings import addSettingsMenu, removeSettingsMenu, pluginSetting, setPluginSetting, readSettings
from qgiscommons.gui import addHelpMenu, removeHelpMenu, addAboutMenu, removeAboutMenu

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
        readSettings()

    def unload(self):
        pem.removePkiTempFiles(self.explorer.catalogs())
        self.explorer.deleteLater()
        removeSettingsMenu("GeoServer", self.iface.removePluginWebMenu)
        removeHelpMenu("GeoServer", self.iface.removePluginWebMenu)
        removeAboutMenu("GeoServer", self.iface.removePluginWebMenu)
        self.iface.removePluginWebMenu(u"GeoServer", self.explorerAction)
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

        self.explorer = GeoServerExplorer()
        self.iface.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.explorer)
        if not pluginSetting("ExplorerVisible"):
            self.explorer.hide()
        self.explorer.visibilityChanged.connect(self._explorerVisibilityChanged)

        addSettingsMenu("GeoServer", self.iface.addPluginToWebMenu)
        addHelpMenu("GeoServer", self.iface.addPluginToWebMenu)
        addAboutMenu("GeoServer", self.iface.addPluginToWebMenu)

        if processingOk:
            Processing.addProvider(self.provider)

        layerwatcher.connectLayerWasAdded(self.explorer)

    def _explorerVisibilityChanged(self, visible):
        setPluginSetting("ExplorerVisible", visible)

    def openExplorer(self):
        self.explorer.show()

