# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
import unittest
import os
import sys
from geoserverexplorer.qgis import layers, catalog
from qgis.core import *
from qgis.utils import iface, QGis
from PyQt4.QtCore import *
from geoserverexplorer.test import utils
from geoserverexplorer.test.utils import PT1, DEM, DEM2, PT1JSON, DEMASCII,\
    GEOLOGY_GROUP, GEOFORMS, LANDUSE, HOOK, WORKSPACE, WORKSPACEB
import re
from .utils import UtilsTestCase


class CatalogTests(UtilsTestCase):
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
        cls.ws = cls.cat.catalog.get_workspace(WORKSPACE)
        assert cls.ws is not None
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
        QgsMapLayerRegistry.instance().removeMapLayer(layer.id())
        self.cat.catalog.delete(self.cat.catalog.get_layer(PT1), recurse=True)
        #TODO: more checking to ensure that the layer in the project is correct


    def testDuplicatedLayerNamesInDifferentWorkSpaces(self):
        """
        Test that when there are more than one layer with
        the same name they can be both added to QGIS
        """
        self.cat.catalog.create_workspace(WORKSPACEB, "http://testb.com")
        wsb = self.cat.catalog.get_workspace(WORKSPACEB)
        self.assertIsNotNone(wsb)

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

        self.assertNotEqual(QgsMapLayerRegistry.instance().mapLayersByName(layer.name()), [])
        self.assertNotEqual(QgsMapLayerRegistry.instance().mapLayersByName(layerb.name()), [])

        QgsMapLayerRegistry.instance().removeMapLayer(layer.id())
        QgsMapLayerRegistry.instance().removeMapLayer(layerb.id())
        self.cat.catalog.delete(self.cat.catalog.get_layer(pt1), recurse=True)
        self.cat.catalog.delete(self.cat.catalog.get_layer(pt1b), recurse=True)


    def testRasterLayerRoundTrip(self):
        self.cat.publishLayer(DEM, self.ws, name = DEM)
        self.assertIsNotNone(self.cat.catalog.get_layer(DEM))
        self.cat.addLayerToProject(DEM, DEM2)
        layer = layers.resolveLayer(DEM2)
        QgsMapLayerRegistry.instance().removeMapLayer(layer.id())
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
        # OGC filter has some fixes in 2.16
        # but it seems that they are now in Boundless 21408 too, so I removed the
        # check for QGIS version and test against latest reference SLD
        sldfile = os.path.join(os.path.dirname(__file__), "resources", "vector.2.16.sld")
        with open(sldfile, 'r') as f:
            sld = f.read()
        gssld = self.cat.catalog.get_style(PT1).sld_body
        self.compareSld(sld, gssld)
        self.cat.catalog.delete(self.cat.catalog.get_layer(PT1), recurse = True)

    def testRasterStylingUpload(self):
        self.cat.publishLayer(DEM, self.ws, name = DEM)
        self.assertIsNotNone(self.cat.catalog.get_layer(DEM))
        sldfile = os.path.join(os.path.dirname(__file__), "resources", "raster.sld")
        with open(sldfile, 'r') as f:
            sld = f.read()
        gssld = self.cat.catalog.get_style(DEM).sld_body
        self.compareSld(sld, gssld)
        self.cat.catalog.delete(self.cat.catalog.get_layer(DEM), recurse = True)

    def testGroup(self):
        self.cat.publishGroup(GEOLOGY_GROUP, workspace = self.ws)
        group = self.cat.catalog.get_layergroup(GEOLOGY_GROUP)
        self.assertIsNotNone(group)
        layers = group.layers
        for layer in layers:
            self.assertIsNotNone(self.cat.catalog.get_layer(layer))
        self.assertTrue(GEOFORMS in layers)
        self.assertTrue(LANDUSE in layers)
        self.cat.catalog.delete(self.cat.catalog.get_layergroup(GEOLOGY_GROUP))
        self.cat.catalog.delete(self.cat.catalog.get_layer(GEOFORMS), recurse = True)
        self.cat.catalog.delete(self.cat.catalog.get_layer(LANDUSE), recurse = True)

    def testPreuploadVectorHook(self):
        if not catalog.processingOk:
            print 'skipping testPreuploadVectorHook, processing not installed'
            return
        settings = QSettings()
        oldHookFile = str(settings.value("/GeoServer/Settings/GeoServer/PreuploadVectorHook", ""))
        hookFile = os.path.join(os.path.dirname(__file__), "resources", "vector_hook.py")
        settings.setValue("/GeoServer/Settings/GeoServer/PreuploadVectorHook", hookFile)
        try:
            hookFile = str(QSettings().value("/GeoServer/Settings/GeoServer/PreuploadVectorHook", ""))
            try:
                self.cat.getAlgorithmFromHookFile(hookFile)
            except:
                raise Exception("Processing hook cannot be executed")
            self.cat.publishLayer(PT1, self.ws, name = HOOK)
            self.assertIsNotNone(self.cat.catalog.get_layer(HOOK))
            self.cat.addLayerToProject(HOOK)
            layer = layers.resolveLayer(HOOK)
            self.assertEqual(1, layer.featureCount())
            QgsMapLayerRegistry.instance().removeMapLayer(layer.id())
        finally:
            settings.setValue("/GeoServer/Settings/GeoServer/PreuploadVectorHook", oldHookFile)
            self.cat.catalog.delete(self.cat.catalog.get_layer(HOOK), recurse = True)

##################################################################################################

def suiteSubset():
    tests = ['testPreuploadVectorHook']
    suite = unittest.TestSuite(map(CatalogTests, tests))
    return suite

def suite():
    suite = unittest.makeSuite(CatalogTests, 'test')
    return suite

# run all tests using unittest skipping nose or testplugin
def run_all():
    # demo_test = unittest.TestLoader().loadTestsFromTestCase(CatalogTests)
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suite())

# run a subset of tests using unittest skipping nose or testplugin
def run_subset():
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suiteSubset())
