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
from geoserverexplorer.test.dragdroptests import DragDropTests
from geoserverexplorer.test import utils

class PkiDragDropTests(DragDropTests):

    '''
    Adapt drag&drop tests to be used in PKI context
    '''
    @classmethod
    def setUpClass(cls):
        # setup auth configuration
        utils.initAuthManager()
        utils.populatePKITestCerts()

        # do workspace popuplation
        super(PkiDragDropTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(PkiDragDropTests, cls).tearDownClass()
        # remove certs
        pem.removeCatalogPkiTempFiles(cls.cat)
        utils.removePKITestCerts()


##################################################################################################

def suiteSubset():
    # set tests you want to execute adding in the following list
    tests = ['testDropVectorLayerUriInCatalogItem']
    suite = unittest.TestSuite(map(PkiDragDropTests, tests))
    return suite

def suite():
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(PkiDragDropTests, 'test'))
    return suite

# run all tests using unittest skipping nose or testplugin
def run_all():
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suite())

# run a subset of tests using unittest skipping nose or testplugin
def run_subset():
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suiteSubset())
