# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
import unittest
import os
import sys
from PyQt4.QtCore import *
from qgis.core import *
from qgis.utils import iface
from geoserverexplorer.geoserver import pem
from geoserverexplorer.test import utils
from geoserverexplorer.test.deletetests import DeleteTests
from geoserverexplorer.test import utils
from qgiscommons2.settings import pluginSetting, setPluginSetting

class PkiDeleteTests(DeleteTests):
    '''
    Adapt delete tests to be used in PKI context
    Class provides additional capabilities to a gsconfig catalog
    Requires a Geoserver catalog running on localhost:8443 with Fra PKI credentials
    '''
    @classmethod
    def setUpClass(cls):
        # setup auth configuration
        utils.initAuthManager()
        utils.populatePKITestCerts()

        # do workspace population
        super(PkiDeleteTests, cls).setUpClass()

        cls.ws = cls.cat.get_workspace(utils.WORKSPACE)
        assert cls.ws is not None

        # load project
        projectFile = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "test.qgs")
        if os.path.normcase(projectFile) != os.path.normcase(QgsProject.instance().fileName()):
            iface.addProject(projectFile)
        # set flags to instruct GUI interaction
        cls.confirmDelete = pluginSetting("ConfirmDelete")
        setPluginSetting("ConfirmDelete", False)

    @classmethod
    def tearDownClass(cls):
        super(PkiDeleteTests, cls).tearDownClass()
        setPluginSetting("ConfirmDelete", cls.confirmDelete)
        # remove certs
        pem.removeCatalogPkiTempFiles(cls.cat)
        utils.removePKITestCerts()

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
