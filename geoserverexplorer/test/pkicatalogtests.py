# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
import unittest
import os
import sys
from qgis.core import *
from qgis.utils import iface 
from geoserverexplorer.geoserver import pem
from geoserverexplorer.test import utils
from geoserverexplorer.test.catalogtests import CatalogTests
from geoserverexplorer.test.utils import WORKSPACE,\
    GSHOSTNAME, GSPORT, GSSSHPORT, GSUSER, GSPASSWORD, \
    AUTHDB_MASTERPWD, AUTHCFGID, AUTHTYPE, AUTH_TESTDATA

class PkiCatalogTests(CatalogTests):
    '''
    Adapt catalog tests to be used in PKI context
    Class provides additional capabilities to a gsconfig catalog
    Requires a Geoserver catalog running on localhost:8443 with Fra PKI credentials
    '''
    @classmethod
    def setUpClass(cls):
        ''' 'test' workspace cannot exist in the test catalog'''
        # setup auth configuration
        os.environ['QGIS_AUTH_DB_DIR_PATH'] = AUTH_TESTDATA
        cls.authm = QgsAuthManager.instance()
        msg = 'Failed to verify master password in auth db'
        assert cls.authm.setMasterPassword(AUTHDB_MASTERPWD, True), msg
        
        # connect and prepare pki catalog
        cls.cat = utils.getGeoServerCatalog(authcfgid=AUTHCFGID, authtype=AUTHTYPE)
        utils.cleanCatalog(cls.cat.catalog)
        cls.cat.catalog.create_workspace(WORKSPACE, "http://geoserver.com")
        cls.ws = cls.cat.catalog.get_workspace(WORKSPACE)
        assert cls.ws is not None
        projectFile = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "test.qgs")
        if os.path.normcase(projectFile) != os.path.normcase(QgsProject.instance().fileName()):
            iface.addProject(projectFile)

    @classmethod
    def tearDownClass(cls):
        utils.cleanCatalog(cls.cat.catalog)
        # remove certs
        pem.removeCatalogPkiTempFiles(cls.cat)

##################################################################################################

def suiteSubset():
    tests = ['testRasterLayerRoundTrip']
    suite = unittest.TestSuite(map(PkiCatalogTests, tests))
    return suite

def suite():
    suite = unittest.makeSuite(PkiCatalogTests, 'test')
    return suite

# run all tests using unittest skipping nose or testplugin
def run_all():
    # demo_test = unittest.TestLoader().loadTestsFromTestCase(PkiCatalogTests)
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suite())

# run a subset of tests using unittest skipping nose or testplugin
def run_subset():
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suiteSubset())
