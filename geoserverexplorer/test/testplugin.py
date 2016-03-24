# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
import unittest
import sys
from geoserverexplorer.test import utils
from geoserverexplorer.test.catalogtests import suite as catalogSuite
from geoserverexplorer.test.deletetests import suite as deleteSuite
from geoserverexplorer.test.dragdroptests import suite as dragdropSuite
from geoserverexplorer.test.guitests import suite as guiSuite

# Tests for the QGIS Tester plugin. To know more see
# https://github.com/boundlessgeo/qgis-tester-plugin

# Tests assume a standard Geoserver at localhost:8080 or GSHOSTNAME:GSPORT
# and default admin/geoserver credentials

def functionalTests():
    try:
        from qgistester.test import Test
    except:
        return []

    dragdropTest = Test("Verify dragging browser element into workspace")
    dragdropTest.addStep("Setting up basic auth context", lambda: utils.setUtilContext(pki=False))
    dragdropTest.addStep("Setting up catalog and explorer", utils.setUpCatalogAndExplorer)
    dragdropTest.addStep("Setting up test data project", utils.loadTestData)
    dragdropTest.addStep("Drag layer from browser 'Project home->qgis_plugin_test_pt1.shp' into\ntest_catalog->Workspaces->test_workspace")
    dragdropTest.addStep("Checking new layer", utils.checkNewLayer)
    dragdropTest.setCleanup(utils.clean)

    vectorRenderingTest = Test("Verify rendering of uploaded style")
    vectorRenderingTest.addStep("Setting up basic auth context", lambda: utils.setUtilContext(pki=False))
    vectorRenderingTest.addStep("Preparing data", utils.openAndUpload)
    vectorRenderingTest.addStep("Check that WMS layer is correctly rendered")
    vectorRenderingTest.setCleanup(utils.clean)

    return [dragdropTest, vectorRenderingTest]

def unitTests():
    _tests = []
    _tests.extend(catalogSuite())
    _tests.extend(deleteSuite())
    _tests.extend(dragdropSuite())
    _tests.extend(guiSuite())
    return _tests

def runAllUnitTests():
    ''' run all unittests - No funcgtional test managed only by Tester Plugin '''
    suite = unittest.TestSuite()
    suite.addTest(catalogSuite())
    suite.addTest(deleteSuite())
    suite.addTest(dragdropSuite())
    suite.addTest(guiSuite())
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suite)
