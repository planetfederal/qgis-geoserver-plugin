# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#

from builtins import object
import os
from geoserverexplorer.gui.explorer import GeoServerExplorer
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *
from qgis import utils 
from qgis.core import QgsMessageLog
from geoserverexplorer.qgis import layerwatcher
from qgiscommons2.settings import pluginSetting, setPluginSetting, readSettings
from qgiscommons2.gui import addHelpMenu, removeHelpMenu, addAboutMenu, removeAboutMenu
from qgiscommons2.gui.settings import addSettingsMenu, removeSettingsMenu

class GeoServerExplorerPlugin(object):

    def __init__(self, iface):
        self.iface = iface
        readSettings()
        try:
            from qgistester.tests import addTestModule
            from geoserverexplorer.test import testplugin
            addTestModule(testplugin, "GeoServer")
        except Exception as ex:
            pass

    def unload(self):
        self.explorer.deleteLater()
        removeSettingsMenu("GeoServer", self.iface.removePluginWebMenu)
        removeHelpMenu("GeoServer", self.iface.removePluginWebMenu)
        removeAboutMenu("GeoServer", self.iface.removePluginWebMenu)
        self.iface.removePluginWebMenu(u"GeoServer", self.explorerAction)
        layerwatcher.disconnectLayerWasAdded()
        try:
            from qgistester.tests import removeTestModule
            from geoserverexplorer.test import testplugin
            removeTestModule(testplugin, "GeoServer")
        except Exception as ex:
            pass

    def initGui(self):
        icon = QIcon(os.path.dirname(__file__) + "/images/geoserver.png")
        self.explorerAction = QAction(icon, "GeoServer Explorer", self.iface.mainWindow())
        self.explorerAction.triggered.connect(self.openExplorer)
        self.iface.addPluginToWebMenu(u"GeoServer", self.explorerAction)

        self.explorer = GeoServerExplorer()
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.explorer)
        if not pluginSetting("ExplorerVisible"):
            self.explorer.hide()
        self.explorer.visibilityChanged.connect(self._explorerVisibilityChanged)

        addSettingsMenu("GeoServer", self.iface.addPluginToWebMenu)
        addHelpMenu("GeoServer", self.iface.addPluginToWebMenu)
        addAboutMenu("GeoServer", self.iface.addPluginToWebMenu)

        layerwatcher.connectLayerWasAdded(self.explorer)

    def _explorerVisibilityChanged(self, visible):
        setPluginSetting("ExplorerVisible", visible)

    def openExplorer(self):
        self.explorer.show()



