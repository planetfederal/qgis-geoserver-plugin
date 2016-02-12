from qgistester.utils import layerFromName
from qgis.core import QgsProject
import qgis.utils
import geoserverexplorer
from geoserverexplorer.geoserver.retry import RetryCatalog
from geoserverexplorer.gui.gsexploreritems import *
from geoserverexplorer.qgis.catalog import CatalogWrapper
import os
from geoserverexplorer.test.utils import geoserverLocation
from geoserverexplorer.test.catalogtests import suite as catalogSuite
from geoserverexplorer.test.deletetests import suite as deleteSuite
from geoserverexplorer.test.dragdroptests import suite as dragdropSuite
from geoserverexplorer.test.guitests import suite as guiSuite


# Tests for the QGIS Tester plugin. To know more see
# https://github.com/boundlessgeo/qgis-tester-plugin

#Tests assume a standard Geoserver at 192.168.0.4:8080 and default admin/geoserver credentials


#Some common methods
#-------------------

def _loadTestData():
    projectFile = os.path.join(os.path.dirname(os.path.abspath(geoserverexplorer.__file__)), "test", "data", "test.qgs")
    if projectFile != QgsProject.instance().fileName():
        qgis.utils.iface.addProject(projectFile)

def _loadSymbologyTestData():
    projectFile = os.path.join(os.path.dirname(os.path.abspath(geoserverexplorer.__file__)), "test", "data", "symbology", "test.qgs")
    if projectFile != QgsProject.instance().fileName():
        qgis.utils.iface.addProject(projectFile)

def _getCatalog():
    return RetryCatalog("http://"+geoserverLocation()+"/geoserver/rest", "admin", "geoserver")

def _setUpCatalogAndWorkspace():
    cat = _getCatalog()
    try:
        _clean()
    except:
        raise
    cat.create_workspace("test_workspace", "http://test.com")
    return cat

def _setUpCatalogAndExplorer():
    explorer = qgis.utils.plugins["geoserverexplorer"].explorer
    explorer.show()
    gsItem = explorer.explorerTree.gsItem
    cat = _setUpCatalogAndWorkspace()
    geoserverItem = GsCatalogItem(cat, "test_catalog")
    gsItem.addChild(geoserverItem)
    geoserverItem.populate()
    gsItem.setExpanded(True)

#TESTS

def _checkNewLayer():
    cat = _getCatalog()
    stores = cat.get_stores("test_workspace")
    assert len(stores) != 0

def _clean():
    cat = _getCatalog()
    ws = cat.get_workspace("test_workspace")
    if ws:
        cat.delete(ws, recurse = True)

def _openAndUpload():
    _loadTestData()
    layer = layerFromName("qgis_plugin_test_pt1")
    cat = _setUpCatalogAndWorkspace()
    catWrapper = CatalogWrapper(cat)
    catWrapper.publishLayer(layer, "test_workspace", True)
    stores = cat.get_stores("test_workspace")
    assert len(stores) != 0
    url = 'url=http://'+geoserverLocation()+'/geoserver/wms&format=image/png&layers=test_workspace:qgis_plugin_test_pt1&styles=qgis_plugin_test_pt1&crs=EPSG:4326'
    wmsLayer = QgsRasterLayer(url, "WMS", 'wms')
    assert wmsLayer.isValid()
    QgsMapLayerRegistry.instance().addMapLayer(wmsLayer)
    qgis.utils.iface.zoomToActiveLayer()

def functionalTests():
    try:
        from qgistester.test import Test
        from qgistester.utils import layerFromName
    except:
        return []

    dragdropTest = Test("Verify dragging browser element into workspace")
    dragdropTest.addStep("Setting up catalog and explorer", _setUpCatalogAndExplorer)
    dragdropTest.addStep("Setting up test data project", _loadTestData)
    dragdropTest.addStep("Drag layer from browser 'Project home->qgis_plugin_test_pt1.shp' into\ntest_catalog->Workspaces->test_workspace")
    dragdropTest.addStep("Checking new layer", _checkNewLayer)
    dragdropTest.setCleanup(_clean)

    vectorRenderingTest = Test("Verify rendering of uploaded style")
    vectorRenderingTest.addStep("Preparing data", _openAndUpload)
    vectorRenderingTest.addStep("Check that WMS layer is correctly rendered")
    vectorRenderingTest.setCleanup(_clean)

    return [dragdropTest, vectorRenderingTest]

def unitTests():
    _tests = []
    _tests.extend(catalogSuite())
    _tests.extend(deleteSuite())
    _tests.extend(dragdropSuite())
    _tests.extend(guiSuite())
    return _tests