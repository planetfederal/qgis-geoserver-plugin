# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
import unittest
from qgis.core import *
import sys
import urllib
from geoserverexplorer.test import utils


class PKIOWSTests(unittest.TestCase):
    '''
    Tests for PKI support in QGIS.

    Requires a Geoserver catalog with pki auth on localhost:8443 with the
    default sample data
    '''

    @classmethod
    def setUpClass(cls):
        """Run before all tests"""
        # setup auth configuration
        utils.initAuthManager()
        utils.populatePKITestCerts()

    @classmethod
    def tearDownClass(cls):
        """Run after all tests"""
        utils.removePKITestCerts()

    def testOpenWFSLayer(self):
        #  https://boundless-test:8443/geoserver/wfs?SERVICE=WFS&VERSION=1.0.0&REQUEST=GetFeature&TYPENAME=usa:states&SRSNAME=EPSG:4326&authcfg=fm1s770
        params = {
            'service': 'WFS',
            'version': '1.0.0',
            'request': 'GetFeature',
            'typename': 'usa:states',
            'srsname': 'EPSG:4326',
            'authcfg':  utils.AUTHCFGID
        }
        uri = 'https://'+utils.geoserverLocationSsh()+'/geoserver/wfs?' + \
              urllib.unquote(urllib.urlencode(params))

        vlayer = QgsVectorLayer(uri, "states", "WFS")
        self.assertTrue(vlayer.isValid())

    def testOpenWMSLayer(self):
        # https://localhost:8443/geoserver/ows?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&BBOX=17.83150900000003602,-179.23023299999996993,71.43776900000000296,-65.1688249999999698&CRS=EPSG:4326&WIDTH=910&HEIGHT=429&LAYERS=usa:states&STYLES=&FORMAT=image/png&DPI=96&MAP_RESOLUTION=96&FORMAT_OPTIONS=dpi:96&TRANSPARENT=TRUE
        quri = QgsDataSourceURI()
        quri.setParam("layers", 'usa:states')
        quri.setParam("styles", '')
        quri.setParam("format", 'image/png')
        quri.setParam("crs", 'EPSG:4326')
        quri.setParam("dpiMode", '7')
        quri.setParam("featureCount", '10')
        quri.setParam("authcfg", utils.AUTHCFGID)
        quri.setParam("contextualWMSLegend", '0')
        quri.setParam("url",
                      'https://'+utils.geoserverLocationSsh()+'/geoserver/wms')

        print str(quri.encodedUri())

        rlayer = QgsRasterLayer(str(quri.encodedUri()), 'states', 'wms')
        self.assertTrue(rlayer.isValid())
        # QgsMapLayerRegistry.instance().addMapLayers([rlayer])

###############################################################################


def suiteSubset():
    tests = ['testOpenWFSLayer']
    suite = unittest.TestSuite(map(PKIOWSTests, tests))
    return suite


def suite():
    suite = unittest.makeSuite(PKIOWSTests, 'test')
    return suite


# run all tests using unittest skipping nose or testplugin
def run_all():
    # demo_test = unittest.TestLoader().loadTestsFromTestCase(PKIOWSTests)
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suite())


# run a subset of tests using unittest skipping nose or testplugin
def run_subset():
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suiteSubset())
