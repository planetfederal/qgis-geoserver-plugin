# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
from builtins import map
import unittest
import os
import sys
from geoserverexplorer.test.utils import PT1, WORKSPACE, WORKSPACEB, STYLE, PT2, PT3,\
    GROUP, GEOLOGY_GROUP, LANDUSE, GEOFORMS
from geoserverexplorer.test.integrationtest import ExplorerIntegrationTest
from geoserverexplorer.qgis import layers

class DragDropTests(ExplorerIntegrationTest):

    #===========================================================================
    # Drag & drop URIs (i.e. from QGIS browser) to a Explorer tree item
    #===========================================================================

    def testDropVectorLayerUriInCatalogItem(self):
        uri = os.path.join(os.path.dirname(__file__), "data", PT1 + ".shp")
        self.catalogItem.acceptDroppedUris(self.tree, self.explorer, [uri])
        layer = self.cat.get_layer(PT1)
        self.assertIsNotNone(layer)
        self.cat.get_stores(PT1, WORKSPACE)[0]
        self.cat.delete(self.cat.get_layer(PT1), recurse = True)
        self.cat.delete(self.cat.get_styles(PT1)[0], purge = True)

    def testDropVectorLayerUriInWorkspaceItem(self):
        uri = os.path.join(os.path.dirname(__file__), "data", PT1 + ".shp")
        item = self.getWorkspaceItem(WORKSPACEB)
        self.assertIsNotNone(item)
        item.acceptDroppedUris(self.tree, self.explorer, [uri])
        layer = self.cat.get_layer(PT1)
        self.assertIsNotNone(layer)
        self.cat.get_stores(PT1, WORKSPACEB)[0]
        self.cat.delete(self.cat.get_layer(PT1), recurse = True)
        self.cat.delete(self.cat.get_styles(PT1)[0], purge = True)

    def testDropVectorLayerUriInLayersItem(self):
        uri = os.path.join(os.path.dirname(__file__), "data", PT1 + ".shp")
        item = self.getLayersItem()
        item.acceptDroppedUris(self.tree, self.explorer, [uri])
        layer = self.cat.get_layer(PT1)
        self.assertIsNotNone(layer)
        self.cat.get_stores(PT1, WORKSPACE)[0]
        self.cat.delete(self.cat.get_layer(PT1), recurse = True)
        self.cat.delete(self.cat.get_styles(PT1)[0], purge = True)

    #===========================================================================
    # Drag & drop explorer tree element(s) into another explorer tree element
    #===========================================================================


    def testDropGsStyleInGsLayerItem(self):
        styleItem = self.getStyleItem(STYLE)
        self.assertIsNotNone(styleItem)
        layerItem = self.getLayerItem(PT2)
        self.assertIsNotNone(layerItem)
        layerItem.acceptDroppedItems(self.tree, self.explorer, [styleItem])
        self.assertIsNotNone(self._getItemUnder(layerItem, STYLE))

    def testDropGsLayerInGsGroupItem(self):
        groupItem = self.getGroupItem(GROUP)
        childCount = groupItem.childCount()
        layerItem = self.getLayerItem(PT3)
        groupItem.acceptDroppedItems(self.tree, self.explorer, [layerItem])
        self.assertEquals(childCount + 1, groupItem.childCount())


##################################################################################################

def suiteSubset():
    # set tests you want to execute adding in the following list
    tests = ['testDropVectorLayerUriInCatalogItem']
    suite = unittest.TestSuite(list(map(DragDropTests, tests)))
    return suite

def suite():
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(DragDropTests, 'test'))
    return suite

# run all tests using unittest skipping nose or testplugin
def run_all():
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suite())

# run a subset of tests using unittest skipping nose or testplugin
def run_subset():
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suiteSubset())
