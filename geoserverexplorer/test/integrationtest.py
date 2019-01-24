# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
from builtins import range
import unittest
from qgis.PyQt.QtCore import QSettings
from geoserverexplorer.gui.explorer import GeoServerExplorer
from geoserverexplorer.test import utils
from geoserverexplorer.gui.gsexploreritems import GsCatalogItem
import os
from qgis.utils import iface
from qgis.core import *
from qgiscommons2.settings import pluginSetting, setPluginSetting

class ExplorerIntegrationTest(unittest.TestCase):
        
    @classmethod
    def setUpClass(cls):
        cls.explorer = GeoServerExplorer()
        # Disable cache
        cls.cache_time = pluginSetting("AuthCatalogXMLCacheTime")
        setPluginSetting("AuthCatalogXMLCacheTime", 1)
        cls.catWrapper = utils.getGeoServerCatalog()
        cls.cat = cls.catWrapper.catalog
        utils.populateCatalog(cls.cat)
        cls.catalogItem = GsCatalogItem(cls.cat, "catalog")
        cls.explorer.explorerTree.gsItem.addChild(cls.catalogItem)
        cls.catalogItem.populate()
        cls.tree = cls.explorer.tree
        projectFile = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "test.qgs")
        iface.addProject(projectFile)

    @classmethod
    def tearDownClass(cls):
        utils.cleanCatalog(cls.cat)
        setPluginSetting("AuthCatalogXMLCacheTime", cls.cache_time)

    def _getItemUnder(self, parent, name):

        def _get_item(name, parent):
            for idx in range(parent.childCount()):
                item = parent.child(idx)
                try:
                    if item.element.name == name:
                        return item
                except:
                    if item.text(0) == name:
                        return item
            return None

        result = _get_item(name, parent)
        if result is None and name.find(':') != -1:
            result = _get_item(name.split(':')[1], parent)
        return result

    def getStoreItem(self, ws, name):
        return self._getItemUnder(self.getWorkspaceItem(ws), name)

    def getWorkspaceItem(self, name):
        return self._getItemUnder(self.getWorkspacesItem(), name)

    def getLayerItem(self, name):
        name = self.cat.get_namespaced_name(name)
        return self._getItemUnder(self.getLayersItem(), name)

    def getGroupItem(self, name):
        return self._getItemUnder(self.getGroupsItem(), name)

    def getStyleItem(self, name):
        return self._getItemUnder(self.getStylesItem(), name)

    def getWorkspacesItem(self):
        return self.catalogItem.child(0)

    def getLayersItem(self):
        return self.catalogItem.child(1)

    def getGroupsItem(self):
        return self.catalogItem.child(2)

    def getStylesItem(self):
        return self.catalogItem.child(3)

    def getGWCLayersItem(self):
        return self.catalogItem.child(4)

    def getGWCLayerItem(self, name):
        return self._getItemUnder(self.getGWCLayersItem(), name)
