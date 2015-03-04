# -*- coding: utf-8 -*-

import sys
import os
import site

site.addsitedir(os.path.abspath(os.path.dirname(__file__) + '/ext-libs'))

from geoserverexplorer.qgis.catalog import *

def classFactory(iface):
    from geoserverexplorer.plugin import GeoServerExplorerPlugin
    return GeoServerExplorerPlugin(iface)
