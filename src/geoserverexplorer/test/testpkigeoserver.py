from qgistester.utils import layerFromName
from geoserverexplorer.gui.gsexploreritems import *

from geoserverexplorer.test.pkicatalogtests import suite as pkiCatalogSuite
from geoserverexplorer.test.pkiowstests import suite as pkiOwsSuite


# Tests for the QGIS Tester plugin. To know more see
# https://github.com/boundlessgeo/qgis-tester-plugin

def unitTests():
    _tests = []
    _tests.extend(pkiCatalogSuite())
    _tests.extend(pkiOwsSuite())
    return _tests