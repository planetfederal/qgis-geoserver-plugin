import unittest
from PyQt4.QtCore import QSettings
from geoserverexplorer.gui.explorer import GeoServerExplorer
from geoserverexplorer.test import utils
from geoserverexplorer.gui.gsexploreritems import GsCatalogItem



class ExplorerIntegrationTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.explorer = GeoServerExplorer()
        cls.catWrapper = utils.getGeoServerCatalog()
        cls.cat = cls.catWrapper.catalog
        utils.populateCatalog(cls.cat)
        cls.catalogItem = GsCatalogItem(cls.cat, "catalog")
        cls.explorer.explorerTree.gsItem.addChild(cls.catalogItem)
        cls.catalogItem.populate()
        cls.tree = cls.explorer.tree
        # @TODO - make tests pass using importer
        cls.useRestApi = QSettings().setValue("/GeoServer/Settings/GeoServer/UseRestApi", True)

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

