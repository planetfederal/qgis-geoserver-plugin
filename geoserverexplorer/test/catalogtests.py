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
from .utils import *
from qgiscommons2.settings import pluginSetting, setPluginSetting
        
class _CatalogTests(UtilsTestCase):
    '''
    Tests for the CatalogWrapper class that provides additional capabilities to a gsconfig catalog
    '''

    @classmethod
    def setUpClass(cls):
        ''' 'test' workspace cannot exist in the test catalog'''
        cls.cat = utils.getGeoServerCatalog()
        utils.cleanCatalog(cls.cat.catalog)
        cls.cat.catalog.create_workspace(WORKSPACE, "http://geoserver.com")
        cls.ws = cls.cat.catalog.get_workspaces(WORKSPACE)[0]        
        projectFile = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "test.qgs")
        iface.addProject(projectFile)

    @classmethod
    def tearDownClass(cls):
        utils.cleanCatalog(cls.cat.catalog)


    def testVectorLayerRoundTrip(self):
        self.cat.publishLayer(PT1, self.ws, name=PT1)
        self.assertIsNotNone(self.cat.catalog.get_layer(PT1))
        self.cat.addLayerToProject(PT1, PT1)
        layer = layers.resolveLayer(PT1)
        QgsProject.instance().removeMapLayer(layer.id())
        self.cat.catalog.delete(self.cat.catalog.get_layer(PT1), recurse=True)
        #TODO: more checking to ensure that the layer in the project is correct


    def testDuplicatedLayerNamesInDifferentWorkSpaces(self):
        """
        Test that when there are more than one layer with
        the same name they can be both added to QGIS
        """
        return
        self.cat.catalog.create_workspace(WORKSPACEB, "http://testb.com")
        wsb = self.cat.catalog.get_workspaces(WORKSPACEB)[0]

        # Need to use prefixed names when retrieving
        pt1 = self.ws.name + ':' + PT1
        pt1b = wsb.name + ':' + PT1
        self.cat.publishLayer(PT1, self.ws, name=PT1)
        self.assertIsNotNone(self.cat.catalog.get_layer(pt1))
        self.cat.addLayerToProject(pt1, pt1)
        layer = layers.resolveLayer(pt1)

        # Add second layer with the same name
        self.cat.publishLayer(PT1, wsb, name=PT1)
        self.assertIsNotNone(self.cat.catalog.get_layer(pt1b))
        self.cat.addLayerToProject(pt1b, pt1b)
        layerb = layers.resolveLayer(pt1b)

        self.assertNotEqual(layer, layerb)
        # Check uris
        self.assertNotEqual(layer.publicSource(), layerb.publicSource())

        self.assertNotEqual(QgsProject.instance().mapLayersByName(layer.name()), [])
        self.assertNotEqual(QgsProject.instance().mapLayersByName(layerb.name()), [])

        QgsProject.instance().removeMapLayer(layer.id())
        QgsProject.instance().removeMapLayer(layerb.id())
        self.cat.catalog.delete(self.cat.catalog.get_layer(pt1), recurse=True)
        self.cat.catalog.delete(self.cat.catalog.get_layer(pt1b), recurse=True)


    def testRasterLayerRoundTrip(self):
        self.cat.publishLayer(DEM, self.ws, name = DEM)
        self.assertIsNotNone(self.cat.catalog.get_layer(DEM))
        self.cat.addLayerToProject(DEM, DEM2)
        layer = layers.resolveLayer(DEM2)
        QgsProject.instance().removeMapLayer(layer.id())
        self.cat.catalog.delete(self.cat.catalog.get_layer(DEM), recurse = True)

    def testVectorLayerUncompatibleFormat(self):
        self.cat.publishLayer(PT1JSON, self.ws, name = PT1JSON)
        self.assertIsNotNone(self.cat.catalog.get_layer(PT1JSON))
        self.cat.catalog.delete(self.cat.catalog.get_layer(PT1JSON), recurse = True)

    def testRasterLayerUncompatibleFormat(self):
        self.cat.publishLayer(DEMASCII, self.ws, name = DEMASCII)
        self.assertIsNotNone(self.cat.catalog.get_layer(DEMASCII))
        self.cat.catalog.delete(self.cat.catalog.get_layer(DEMASCII), recurse = True)

    def compareSld(self, a, b):
        a = a.replace("\r", "").replace("\n", "").replace(" ", "")
        b = b.replace("\r", "").replace("\n", "").replace(" ", "")
        a = re.sub(r"<sld:StyledLayerDescriptor.*?>", "", a)
        b = re.sub(r"<sld:StyledLayerDescriptor.*?>", "", b)
        a = re.sub(r"<ogc:Literal>(\d+)\.(\d+)</ogc:Literal>", r"<ogc:Literal>\1</ogc:Literal>", a)
        b = re.sub(r"<ogc:Literal>(\d+)\.(\d+)</ogc:Literal>", r"<ogc:Literal>\1</ogc:Literal>", b)
        self.assertXMLEqual(a, b, "SLD compare failed %s\n%s" % (a, b))

    def testVectorStylingUpload(self):
        self.cat.publishLayer(PT1, self.ws, name = PT1)
        self.assertIsNotNone(self.cat.catalog.get_layer(PT1))
        sldfile = os.path.join(os.path.dirname(__file__), "resources", "vector.2.16.sld")
        with open(sldfile, 'r') as f:
            sld = f.read()
        gssld = self.cat.catalog.get_styles(PT1)[0].sld_body.decode()
        self.compareSld(sld, gssld)
        self.cat.catalog.delete(self.cat.catalog.get_layer(PT1), recurse = True)

    def testRasterStylingUpload(self):
        self.cat.publishLayer(DEM, self.ws, name = DEM)
        self.assertIsNotNone(self.cat.catalog.get_layer(DEM))
        sldfile = os.path.join(os.path.dirname(__file__), "resources", "raster.sld")
        with open(sldfile, 'r') as f:
            sld = f.read()
        gssld = self.cat.catalog.get_styles(DEM)[0].sld_body.decode()
        self.compareSld(sld, gssld)
        self.cat.catalog.delete(self.cat.catalog.get_layer(DEM), recurse = True)

    def testUploadRenameAndDownload(self):
        QgsNetworkAccessManager.instance().cache().clear()
        self.cat.publishLayer(PT1, self.ws, name = PT1)
        self.assertIsNotNone(self.cat.catalog.get_layer(PT1))
        self.cat.addLayerToProject(PT1, PT1 + "_fromGeoserver")
        layer = layers.resolveLayer(PT1 + "_fromGeoserver")
        self.cat.publishLayer(PT1, self.ws, name = PT1 + "b")
        self.cat.addLayerToProject(PT1 + "b", PT1 + "b_fromGeoserver")
        layer = layers.resolveLayer(PT1 + "b_fromGeoserver")
        self.cat.catalog.delete(self.cat.catalog.get_layer(PT1), recurse = True)
        self.cat.catalog.delete(self.cat.catalog.get_layer(PT1 + "b"), recurse = True)



##################################################################################################

class CatalogTestsAuth(_CatalogTests):
    
    @classmethod
    def setUpClass(cls):
        enableAuth()
        super().setUpClass()

class CatalogTestsNoAuth(_CatalogTests):

    @classmethod
    def setUpClass(cls):
        disableAuth()
        super().setUpClass()

def suiteAuth():
    suite = unittest.makeSuite(CatalogTestsAuth, 'test')
    return suite

def suiteNoAuth():
    suite = unittest.makeSuite(CatalogTestsNoAuth, 'test')
    return suite

# run all tests using unittest skipping nose or testplugin
def run_all():
    # demo_test = unittest.TestLoader().loadTestsFromTestCase(CatalogTests)
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suiteAuth())
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suiteNoAuth())

# run a subset of tests using unittest skipping nose or testplugin
def run_subset():
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suiteSubset())


