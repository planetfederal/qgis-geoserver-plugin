import unittest
import os
import sys
from geoserverexplorer.geoserver import pem
from qgis.core import *
from geoserverexplorer.test import utils
from geoserverexplorer.test.pkitests import PkiTests
from geoserverexplorer.test.catalogtests import CatalogTests
from geoserverexplorer.test.utils import WORKSPACE,\
    GSHOSTNAME, GSPORT, GSSSHPORT, GSUSER, GSPASSWORD, \
    AUTHDB_MASTERPWD, AUTHCFGID, AUTHTYPE, AUTH_TESTDATA

class PkiCatalogTests(PkiTests, CatalogTests):
    '''
    Adapt catalog tests to be used in PKI context
    '''

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
