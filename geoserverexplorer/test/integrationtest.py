# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
import unittest
from PyQt4.QtCore import QSettings
from geoserverexplorer.gui.explorer import GeoServerExplorer
from geoserverexplorer.test import utils
from geoserverexplorer.gui.gsexploreritems import GsCatalogItem
import os
from qgis.utils import iface
from qgis.core import *
from geoserverexplorer.test.utils import AUTHCFGID, AUTHTYPE


class ExplorerIntegrationTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.explorer = GeoServerExplorer()
        # check if context is a PKI auth context
        if hasattr(cls, 'authm') and cls.authm:
            cls.catWrapper = utils.getGeoServerCatalog(authcfgid=AUTHCFGID, authtype=AUTHTYPE)
        else:
            cls.catWrapper = utils.getGeoServerCatalog()
        cls.cat = cls.catWrapper.catalog
        utils.populateCatalog(cls.cat)
        cls.catalogItem = GsCatalogItem(cls.cat, "catalog")
        cls.explorer.explorerTree.gsItem.addChild(cls.catalogItem)
        cls.catalogItem.populate()
        cls.tree = cls.explorer.tree
        # @TODO - make tests pass using importer
        cls.useRestApi = QSettings().setValue("/GeoServer/Settings/GeoServer/UseRestApi", True)
        projectFile = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "test.qgs")
        if os.path.normcase(projectFile) != os.path.normcase(QgsProject.instance().fileName()):
            iface.addProject(projectFile)

    @classmethod
    def tearDownClass(cls):
        utils.cleanCatalog(cls.cat)

    def _getItemUnder(self, parent, name):
        for idx in range(parent.childCount()):
            item = parent.child(idx)
            if item.text(0) == name:
                return item

    def getStoreItem(self, ws, name):
        return self._getItemUnder(self.getWorkspaceItem(ws), name)

    def getWorkspaceItem(self, name):
        return self._getItemUnder(self.getWorkspacesItem(), name)

    def getLayerItem(self, name):
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

