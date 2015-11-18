import unittest
import os
import sys
from PyQt4.QtCore import *
from qgis.core import *
from qgis.utils import iface
from geoserverexplorer.test.utils import PT1, safeName, PT2, WORKSPACE, shapefile_and_friends
from geoserverexplorer.test.integrationtest import ExplorerIntegrationTest
from geoserverexplorer.qgis import layers


class DeleteTests(ExplorerIntegrationTest):

    @classmethod
    def setUpClass(cls):
        # do workspace popuplation
        super(DeleteTests, cls).setUpClass()

        cls.ws = cls.cat.get_workspace(WORKSPACE)
        assert cls.ws is not None
        
        # load project
        projectFile = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "test.qgs")
        if os.path.normcase(projectFile) != os.path.normcase(QgsProject.instance().fileName()):
            iface.addProject(projectFile)
        # set flags to instruct GUI interaction
        cls.confirmDelete = QSettings().value("/GeoServer/Settings/General/ConfirmDelete", True, bool)
        QSettings().setValue("/GeoServer/Settings/General/ConfirmDelete", False)

    @classmethod
    def tearDownClass(cls):
        super(DeleteTests, cls).tearDownClass()
        QSettings().setValue("/GeoServer/Settings/General/ConfirmDelete", cls.confirmDelete)

    def testDeleteLayerAndStyle(self):
        settings = QSettings()
        # step 1: publish a layer. publish load layer and style
        self.catWrapper.publishLayer(PT1, self.ws, name = PT1)
        layer = self.cat.get_layer(PT1)
        self.assertIsNotNone(layer)
        style = self.cat.get_style(PT1)
        self.assertIsNotNone(style)
        self.getLayersItem().refreshContent(self.explorer)
        self.getStylesItem().refreshContent(self.explorer)
        # step 2: set flag to remove also style
        deleteStyle = bool(settings.value("/GeoServer/Settings/GeoServer/DeleteStyle"))
        settings.setValue("/GeoServer/Settings/GeoServer/DeleteStyle", True)
        # step 3: then remove layer and style 
        layerItem = self.getLayerItem(PT1)
        layerItem.deleteLayer(self.tree, self.explorer)
        layerItem = self.getLayerItem(PT1)
        self.assertIsNone(layerItem)
        styleItem = self.getStyleItem(PT1)
        self.assertIsNone(styleItem)
        # step 4: republish PT1 and it's style
        self.catWrapper.publishLayer(PT1, self.ws, name = PT1)
        layer = self.cat.get_layer(PT1)
        self.assertIsNotNone(layer)
        style = self.cat.get_style(PT1)
        self.assertIsNotNone(style)
        self.getLayersItem().refreshContent(self.explorer)
        self.getStylesItem().refreshContent(self.explorer)
        # step 5: set flag to remove layer BUT not style
        settings.setValue("/GeoServer/Settings/GeoServer/DeleteStyle", False)
        # step 6: remove layer and check style is not erased
        layerItem = self.getLayerItem(PT1)
        layerItem.deleteLayer(self.tree, self.explorer)
        layerItem = self.getLayerItem(PT1)
        self.assertIsNone(layerItem)
        styleItem = self.getStyleItem(PT1)
        self.assertIsNotNone(styleItem)
        # step 7: then remove style
        styleItem.deleteStyle(self.tree, self.explorer)
        styleItem = self.getStyleItem(PT1)
        self.assertIsNone(styleItem)
        # step 8: set flag in original mode
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
    
    def testDeleteStyle(self):
        ''' TODO: test deleting only style.
            delete only if not used in other layers
        '''
        pass
        
##################################################################################################

def suiteSubset():
    tests = ['testDeleteLayerAndStyle']
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
