import unittest
import os
import sys
from PyQt4.QtCore import *
from qgis.core import *
from qgis.utils import iface 
from geoserverexplorer.geoserver import pem
from geoserverexplorer.test import utils
from geoserverexplorer.test.deletetests import DeleteTests
from geoserverexplorer.test.utils import WORKSPACE,\
    GSHOSTNAME, GSPORT, GSSSHPORT, GSUSER, GSPASSWORD, \
    AUTHDB_MASTERPWD, AUTHCFGID, AUTHTYPE, AUTH_TESTDATA

class PkiDeleteTests(DeleteTests):
    '''
    Adapt delete tests to be used in PKI context
    Class provides additional capabilities to a gsconfig catalog
    Requires a Geoserver catalog running on localhost:8443 with Fra PKI credentials
    '''
    @classmethod
    def setUpClass(cls):
        # setup auth configuration
        os.environ['QGIS_AUTH_DB_DIR_PATH'] = AUTH_TESTDATA
        cls.authm = QgsAuthManager.instance()
        msg = 'Failed to verify master password in auth db'
        assert cls.authm.setMasterPassword(AUTHDB_MASTERPWD, True), msg
        
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
        # remove certs
        pem.removeCatalogPkiTempFiles(cls.cat)

##################################################################################################

def suiteSubset():
    tests = ['testDeleteLayerAndStyle']
    suite = unittest.TestSuite(map(PkiDeleteTests, tests))
    return suite

def suite():
    suite = unittest.makeSuite(PkiDeleteTests, 'test')
    return suite

# run all tests using unittest skipping nose or testplugin
def run_all():
    # demo_test = unittest.TestLoader().loadTestsFromTestCase(PkiDeleteTests)
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suite())

# run a subset of tests using unittest skipping nose or testplugin
def run_subset():
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suiteSubset())
