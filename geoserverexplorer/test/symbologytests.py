# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
from builtins import map
import unittest
import os
import sys
from geoserverexplorer.qgis import layers, catalog
from geoserverexplorer.qgis.sldadapter import adaptGsToQgs,\
    getGsCompatibleSld
from qgis.core import *
from qgis.utils import iface
from qgis.PyQt.QtCore import *
from geoserverexplorer.test import utils
from geoserverexplorer.test.utils import PT1, DEM, DEM2, PT1JSON, DEMASCII,\
    GEOLOGY_GROUP, GEOFORMS, LANDUSE, HOOK, WORKSPACE, WORKSPACEB
import re

class SymbologyTests(unittest.TestCase):
    '''
    Tests for the CatalogWrapper class that provides additional capabilities to a gsconfig catalog
    Requires a Geoserver catalog running on localhost:8080 with default credentials
    '''

    @classmethod
    def setUpClass(cls):
        ''' 'test' workspace cannot exist in the test catalog'''
        cls.cat = utils.getGeoServerCatalog()
        utils.cleanCatalog(cls.cat.catalog)
        cls.cat.catalog.create_workspace(WORKSPACE, "http://geoserver.com")
        cls.ws = cls.cat.catalog.get_workspaces(WORKSPACE)[0]        
        projectFile = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "test_font.qgs")
        iface.addProject(projectFile)

    @classmethod
    def tearDownClass(cls):
        utils.cleanCatalog(cls.cat.catalog)

    def testVectorFontStylingUpload(self):
        layer = layers.resolveLayer(PT1)
        sld, icons = getGsCompatibleSld(layer)
        self.assertTrue("<WellKnownName>ttf://DejaVu Sans#0x46</WellKnownName>" in sld)

##################################################################################################


def suite():
    suite = unittest.makeSuite(SymbologyTests, 'test')
    return suite

# run all tests using unittest skipping nose or testplugin
def run_all():
    # demo_test = unittest.TestLoader().loadTestsFromTestCase(CatalogTests)
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suite())

# run a subset of tests using unittest skipping nose or testplugin
def run_subset():
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suiteSubset())
