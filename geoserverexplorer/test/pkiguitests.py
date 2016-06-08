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
from geoserverexplorer.geoserver import pem
from geoserverexplorer.test.guitests import CreateCatalogDialogTests
from geoserverexplorer.test.guitests import GroupDialogTests
from geoserverexplorer.test.guitests import LayerDialogTests
from geoserverexplorer.test.guitests import GsNameUtilsTest
from geoserverexplorer.test.guitests import GSNameDialogTest
from geoserverexplorer.test import utils


class PkiCreateCatalogDialogTests(CreateCatalogDialogTests):
    '''
    Adapt tests to be used in PKI context
    '''
    @classmethod
    def setUpClass(cls):
        # setup auth configuration
        utils.initAuthManager()
        utils.populatePKITestCerts()

    @classmethod
    def tearDownClass(cls):
        super(PkiCreateCatalogDialogTests, cls).tearDownClass()
        utils.removePKITestCerts()


class PkiGroupDialogTests(GroupDialogTests):
    '''
    Adapt tests to be used in PKI context
    '''
    @classmethod
    def setUpClass(cls):
        # setup auth configuration
        utils.initAuthManager()
        utils.populatePKITestCerts()

        super(PkiGroupDialogTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(PkiGroupDialogTests, cls).tearDownClass()
        # remove certs
        pem.removeCatalogPkiTempFiles(cls.cat)
        utils.removePKITestCerts()


class PkiLayerDialogTests(LayerDialogTests):
    '''
    Adapt tests to be used in PKI context
    '''
    @classmethod
    def setUpClass(cls):
        # setup auth configuration
        utils.initAuthManager()
        utils.populatePKITestCerts()

        super(PkiLayerDialogTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(LayerDialogTests, cls).tearDownClass()
        # remove certs
        pem.removeCatalogPkiTempFiles(cls.cat)
        utils.removePKITestCerts()


class PkiGsNameUtilsTest(GsNameUtilsTest):
    '''
    Adapt tests to be used in PKI context
    '''
    @classmethod
    def setUpClass(cls):
        # setup auth configuration
        utils.initAuthManager()
        utils.populatePKITestCerts()

    @classmethod
    def tearDownClass(cls):
        super(PkiGsNameUtilsTest, cls).tearDownClass()
        utils.removePKITestCerts()


class PkiGSNameDialogTest(GSNameDialogTest):
    '''
    Adapt tests to be used in PKI context
    '''
    @classmethod
    def setUpClass(cls):
        # setup auth configuration
        utils.initAuthManager()
        utils.populatePKITestCerts()

    @classmethod
    def tearDownClass(cls):
        super(PkiGSNameDialogTest, cls).tearDownClass()
        utils.removePKITestCerts()

###############################################################################


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
