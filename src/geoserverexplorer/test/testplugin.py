import qgis.utils
import geoserverexplorer
from geoserverexplorer.geoserver.retry import RetryCatalog
from geoserverexplorer.gui.gsexploreritems import *
from geoserverexplorer.qgis.catalog import CatalogWrapper
import os
from geoserverexplorer.test.catalogtests import suite as catalogSuite
from geoserverexplorer.test.deletetests import suite as deleteSuite
#from geoserverexplorer.test.dragdroptests import suite as dragdropSuite
from geoserverexplorer.test.guitests import suite as guiSuite
#from geoserverexplorer.test.integrationtest import suite as integrationSuite
#from geoserverexplorer.test.pkitests import suite as pkiSuite


#Tests assume a standard Geoserver at localhost:8080 and default admin/geoserver credentials

try:
    from qgistester.tests import addTestModule
    addTestModule(__module__)
except:
    pass
#Some common methods

def _loadTestData():
    projectFile = os.path.join(os.path.dirname(os.path.abspath(geoserverexplorer.__file__)), "test", "data", "test.qgs")
    if projectFile != QgsProject.instance().fileName():
        qgis.utils.iface.addProject(projectFile)

def _loadSymbologyTestData():
    projectFile = os.path.join(os.path.dirname(os.path.abspath(geoserverexplorer.__file__)), "test", "data", "symbology", "test.qgs")
    if projectFile != QgsProject.instance().fileName():
        qgis.utils.iface.addProject(projectFile)

def _getCatalog():
    return RetryCatalog("http://localhost:8080/geoserver/rest", "admin", "geoserver")

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
    url = 'url=http://localhost:8080/geoserver/wms&format=image/png&layers=test_workspace:qgis_plugin_test_pt1&styles=qgis_plugin_test_pt1&crs=EPSG:4326'
    wmsLayer = QgsRasterLayer(url, "WMS", 'wms')
    assert wmsLayer.isValid()
    QgsMapLayerRegistry.instance().addMapLayer(wmsLayer)

def functionalTests():
    try:
        from qgistester.test import Test
        from qgistester.utils import layerFromName
    except:
        return []

    dragdropTest = Test("Verify dragging browser element into workspace")
    dragdropTest.addStep("Setting up catalog and explorer", _setUpCatalogAndExplorer)
    dragdropTest.addStep("Drag layer from browser into testing workspace of testing catalog")
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
    #_tests.extend(dragdropSuite())
    #_tests.extend(guiSuite())
    #_tests.extend(integrationSuite())
    #_tests.extend(pkiSuite())
    return _tests 