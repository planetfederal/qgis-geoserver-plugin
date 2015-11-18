from geoserverexplorer.test.utils import PT1, safeName, PT2, WORKSPACE
from geoserverexplorer.test.integrationtest import ExplorerIntegrationTest
import unittest
import sys
from PyQt4.QtCore import *
from geoserverexplorer.qgis import layers


class DeleteTests(ExplorerIntegrationTest):

    @classmethod
    def setUpClass(cls):
        super(DeleteTests, cls).setUpClass()
        cls.confirmDelete = QSettings().value("/GeoServer/Settings/General/ConfirmDelete", True, bool)
        QSettings().setValue("/GeoServer/Settings/General/ConfirmDelete", False)

    @classmethod
    def tearDownClass(cls):
        super(DeleteTests, cls).tearDownClass()
        QSettings().setValue("/GeoServer/Settings/General/ConfirmDelete", cls.confirmDelete)

    def testDeleteLayerAndStyle(self):
        settings = QSettings()
        layerItem = self.getLayerItem(PT1)
        wsItem = self.getWorkspacesItem()
        wsItem.acceptDroppedItems(self.tree, self.explorer, [layerItem])
        layer = self.cat.get_layer(PT1)
        self.assertIsNotNone(layer)
        self.getLayersItem().refreshContent(self.explorer)
        self.getStylesItem().refreshContent(self.explorer)
        deleteStyle = bool(settings.value("/GeoServer/Settings/GeoServer/DeleteStyle"))
        settings.setValue("/GeoServer/Settings/GeoServer/DeleteStyle", True)
        layerItem = self.getLayerItem(PT1)
        layerItem.deleteLayer(self.tree, self.explorer)
        layerItem = self.getLayerItem(PT1)
        self.assertIsNone(layerItem)
        styleItem = self.getStyleItem(PT1)
        self.assertIsNone(styleItem)
        layerItem = self.getLayerItem(PT1)
        wsItem = self.getWorkspacesItem()
        wsItem.acceptDroppedItems(self.tree, self.explorer, [layerItem])
        layer = self.cat.get_layer(PT1)
        self.assertIsNotNone(layer)
        self.getLayersItem().refreshContent(self.explorer)
        self.getStylesItem().refreshContent(self.explorer)
        settings.setValue("/GeoServer/Settings/GeoServer/DeleteStyle", False)
        layerItem = self.getLayerItem(PT1)
        layerItem.deleteLayer(self.tree, self.explorer)
        layerItem = self.getLayerItem(PT1)
        self.assertIsNone(layerItem)
        styleItem = self.getStyleItem(PT1)
        self.assertIsNotNone(styleItem)
        styleItem.deleteStyle(self.tree, self.explorer)
        styleItem = self.getStyleItem(PT1)
        self.assertIsNone(styleItem)
        settings.setValue("/GeoServer/Settings/GeoServer/DeleteStyle", deleteStyle)


    def testDeleteWorkspace(self):
        wsname = safeName("another_workspace")
        self.cat.create_workspace(wsname, "http://anothertesturl.com")
        self.getWorkspacesItem().refreshContent(self.explorer)
        wsItem = self.getWorkspaceItem(wsname)
        wsItem.deleteWorkspace(self.tree, self.explorer)
        self.getWorkspacesItem().refreshContent(self.explorer)
        wsItem = self.getWorkspaceItem(wsname)
        self.assertIsNone(wsItem)
        ws = self.cat.get_workspace(wsname)
        self.assertIsNone(ws)


    def testDeleteGWCLayer(self):
        name = WORKSPACE + ":" + PT2
        item = self.getGWCLayerItem(name)
        item.deleteLayer(self.explorer)
        item = self.getGWCLayerItem(name)
        self.assertIsNone(item)


##################################################################################################

def suiteSubset():
    tests = ['name of the test to execute']
    suite = unittest.TestSuite(map(DeleteTests, tests))
    return suite

def suite():
    suite = unittest.makeSuite(DeleteTests, 'test')
    return suite

# run all tests using unittest skipping nose or testplugin
def run_all():
    # demo_test = unittest.TestLoader().loadTestsFromTestCase(DeleteTests)
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suite())

# run a subset of tests using unittest skipping nose or testplugin
def run_subset():
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suiteSubset())
