# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
from builtins import map
import unittest
import os
import sys
from qgis.PyQt.QtCore import *
from qgis.core import *
from qgis.utils import iface
from geoserverexplorer.test.utils import PT1, safeName, PT2, WORKSPACE, WORKSPACEB, shapefile_and_friends
from geoserverexplorer.test.integrationtest import ExplorerIntegrationTest
from geoserverexplorer.qgis import layers
from qgiscommons2.settings import pluginSetting, setPluginSetting

class DeleteTests(ExplorerIntegrationTest):

    @classmethod
    def setUpClass(cls):
        # do workspace popuplation
        super(DeleteTests, cls).setUpClass()

        cls.ws = cls.cat.get_workspaces(WORKSPACE)[0]        

        # load project
        projectFile = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "test.qgs")
        if os.path.normcase(projectFile) != os.path.normcase(QgsProject.instance().fileName()):
            iface.addProject(projectFile)
        # set flags to instruct GUI interaction
        cls.confirmDelete = pluginSetting("ConfirmDelete")
        setPluginSetting("ConfirmDelete", False)

    @classmethod
    def tearDownClass(cls):
        super(DeleteTests, cls).tearDownClass()
        setPluginSetting("ConfirmDelete", cls.confirmDelete)

    def testDeleteLayerAndStyle(self):
        # step 1: publish a layer. publish load layer and style
        self.catWrapper.publishLayer(PT1, self.ws, name=PT1)
        layer = self.cat.get_layer(PT1)
        self.assertIsNotNone(layer)
        style = self.cat.get_styles(PT1)[0]
        self.assertIsNotNone(style)
        self.getLayersItem().refreshContent(self.explorer)
        self.getStylesItem().refreshContent(self.explorer)
        # step 2: set flag to remove also style
        deleteStyle = pluginSetting("DeleteStyle")
        setPluginSetting("DeleteStyle", True)
        # step 3: then remove layer and style
        layerItem = self.getLayerItem(PT1)
        self.assertIsNotNone(layerItem)
        layerItem.deleteLayer(self.tree, self.explorer)
        layerItem = self.getLayerItem(PT1)
        self.assertIsNone(layerItem)
        styleItem = self.getStyleItem(PT1)
        self.assertIsNone(styleItem)
        # step 4: republish PT1 and it's style
        self.catWrapper.publishLayer(PT1)
        layer = self.cat.get_layer(PT1)
        self.assertIsNotNone(layer)
        style = self.cat.get_styles(PT1)[0]
        self.assertIsNotNone(style)
        self.getLayersItem().refreshContent(self.explorer)
        self.getStylesItem().refreshContent(self.explorer)
        # step 5: set flag to remove layer BUT not style
        setPluginSetting("DeleteStyle", False)
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
        setPluginSetting("DeleteStyle", deleteStyle)

    def testDeleteLayersWithSameName(self):
        """
        Test that when there are more than one layer with
        the same name they can be deleted
        """
        wsb = self.catWrapper.catalog.get_workspaces(WORKSPACEB)[0]        

        # Need to use prefixed names when retrieving
        pt1 = self.ws.name + ':' + PT1
        pt1b = wsb.name + ':' + PT1
        self.catWrapper.publishLayer(PT1, self.ws, name=PT1)
        self.assertIsNotNone(self.catWrapper.catalog.get_layer(pt1))

        # Add second layer with the same name
        self.catWrapper.publishLayer(PT1, wsb, name=PT1)
        self.assertIsNotNone(self.catWrapper.catalog.get_layer(pt1b))

        self.getLayersItem().refreshContent(self.explorer)

        # step 3: then remove layers
        layerItem = self.getLayerItem(pt1)
        self.assertIsNotNone(layerItem)
        layerItem.deleteLayer(self.tree, self.explorer)
        layerItem = self.getLayerItem(pt1)
        self.assertIsNone(layerItem)

        layerItem = self.getLayerItem(pt1b)
        self.assertIsNotNone(layerItem)
        layerItem.deleteLayer(self.tree, self.explorer)
        layerItem = self.getLayerItem(pt1b)
        self.assertIsNone(layerItem)


    def testDeleteWorkspace(self):
        wsname = safeName("another_workspace")
        self.cat.create_workspace(wsname, "http://anothertesturl.com")
        self.getWorkspacesItem().refreshContent(self.explorer)
        wsItem = self.getWorkspaceItem(wsname)
        wsItem.deleteWorkspace(self.tree, self.explorer)
        self.getWorkspacesItem().refreshContent(self.explorer)
        wsItem = self.getWorkspaceItem(wsname)
        self.assertIsNone(wsItem)
        ws = self.cat.get_workspaces(wsname)
        self.assertTrue(len(ws) == 0 )


    def testDeleteGWCLayer(self):
        name = WORKSPACE + ":" + PT2
        item = self.getGWCLayerItem(name)
        item.deleteLayer(self.explorer)
        item = self.getGWCLayerItem(name)
        self.assertIsNone(item)


##################################################################################################

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
