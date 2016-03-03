import unittest
import os
import sys
from PyQt4.QtCore import *
from qgis.core import *
from geoserverexplorer.geoserver import pem
from geoserverexplorer.test.guitests import CreateCatalogDialogTests
from geoserverexplorer.test.guitests import GroupDialogTests
from geoserverexplorer.test.guitests import LayerDialogTests
from geoserverexplorer.test.guitests import GsNameUtilsTest
from geoserverexplorer.test.guitests import GSNameDialogTest
from geoserverexplorer.test.utils import AUTHDB_MASTERPWD, AUTHCFGID, AUTHTYPE, AUTH_TESTDATA

class PkiCreateCatalogDialogTests(CreateCatalogDialogTests):
    '''
    Adapt tests to be used in PKI context
    '''
    @classmethod
    def setUpClass(cls):
        # setup auth configuration
        os.environ['QGIS_AUTH_DB_DIR_PATH'] = AUTH_TESTDATA
        cls.authm = QgsAuthManager.instance()
        msg = 'Failed to verify master password in auth db'
        assert cls.authm.setMasterPassword(AUTHDB_MASTERPWD, True), msg

    @classmethod
    def tearDownClass(cls):
        super(PkiCreateCatalogDialogTests, cls).tearDownClass()

class PkiGroupDialogTests(GroupDialogTests):
    '''
    Adapt tests to be used in PKI context
    '''
    @classmethod
    def setUpClass(cls):
        # setup auth configuration
        os.environ['QGIS_AUTH_DB_DIR_PATH'] = AUTH_TESTDATA
        cls.authm = QgsAuthManager.instance()
        msg = 'Failed to verify master password in auth db'
        assert cls.authm.setMasterPassword(AUTHDB_MASTERPWD, True), msg

        super(PkiGroupDialogTests, cls).setUpClass()
        
    @classmethod
    def tearDownClass(cls):
        super(PkiGroupDialogTests, cls).tearDownClass()
        # remove certs
        pem.removeCatalogPkiTempFiles(cls.cat)

class PkiLayerDialogTests(LayerDialogTests):
    '''
    Adapt tests to be used in PKI context
    '''
    @classmethod
    def setUpClass(cls):
        # setup auth configuration
        os.environ['QGIS_AUTH_DB_DIR_PATH'] = AUTH_TESTDATA
        cls.authm = QgsAuthManager.instance()
        msg = 'Failed to verify master password in auth db'
        assert cls.authm.setMasterPassword(AUTHDB_MASTERPWD, True), msg

        super(PkiLayerDialogTests, cls).setUpClass()
        
    @classmethod
    def tearDownClass(cls):
        super(LayerDialogTests, cls).tearDownClass()
        # remove certs
        pem.removeCatalogPkiTempFiles(cls.cat)

class PkiGsNameUtilsTest(GsNameUtilsTest):
    '''
    Adapt tests to be used in PKI context
    '''
    @classmethod
    def setUpClass(cls):
        # setup auth configuration
        os.environ['QGIS_AUTH_DB_DIR_PATH'] = AUTH_TESTDATA
        cls.authm = QgsAuthManager.instance()
        msg = 'Failed to verify master password in auth db'
        assert cls.authm.setMasterPassword(AUTHDB_MASTERPWD, True), msg
        
    @classmethod
    def tearDownClass(cls):
        super(PkiGsNameUtilsTest, cls).tearDownClass()

class PkiGSNameDialogTest(GSNameDialogTest):
    '''
    Adapt tests to be used in PKI context
    '''
    @classmethod
    def setUpClass(cls):
        # setup auth configuration
        os.environ['QGIS_AUTH_DB_DIR_PATH'] = AUTH_TESTDATA
        cls.authm = QgsAuthManager.instance()
        msg = 'Failed to verify master password in auth db'
        assert cls.authm.setMasterPassword(AUTHDB_MASTERPWD, True), msg
        
    @classmethod
    def tearDownClass(cls):
        super(PkiGSNameDialogTest, cls).tearDownClass()

##################################################################################################

def suiteSubset():
    tests = ['testCreateCatalogDialog']
    suite = unittest.TestSuite(map(PkiCreateCatalogDialogTests, tests))
    return suite

def suite():
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(PkiCreateCatalogDialogTests, 'test'))
    suite.addTests(unittest.makeSuite(PkiGroupDialogTests, 'test'))
    suite.addTests(unittest.makeSuite(PkiLayerDialogTests, 'test'))
    suite.addTests(unittest.makeSuite(PkiGsNameUtilsTest, 'test'))
    suite.addTests(unittest.makeSuite(PkiGSNameDialogTest, 'test'))
    return suite

# run all tests using unittest skipping nose or testplugin
def run_all():
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suite())

# run a subset of tests using unittest skipping nose or testplugin
def run_subset():
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suiteSubset())
