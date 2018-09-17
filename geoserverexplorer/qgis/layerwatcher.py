# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
from geoserverexplorer.qgis.utils import isTrackedLayer
from geoserverexplorer.qgis import uri as uri_utils
from geoserverexplorer.qgis.sldadapter import adaptGsToQgs
from qgis.core import *
from qgis.gui import *
from qgis.utils import iface
from geoserverexplorer.qgis.utils import readTrackedLayers
from functools import partial
from qgis.PyQt import QtCore, QtGui, QtWidgets
from geoserverexplorer.qgis.utils import getTrackingInfo, removeTrackedLayer
from geoserver.catalog import Catalog
from geoserverexplorer.qgis.catalog import CatalogWrapper
from qgiscommons2.settings import pluginSetting
from qgiscommons2.files import tempFilename
from geoserverexplorer.gui import setInfo, setWarning, setError

_explorer = None

def layerAdded(qgislayer):
    try:
        if qgislayer.providerType().lower() != "wfs":
            return
    except:
        pass #Not all layers have a providerType method
    catalogs = list(_explorer.explorerTree.gsItem._catalogs.values())
    for cat in catalogs:
        if cat.layersEndpointUrl() in qgislayer.source():
            for layer in cat.get_layers():
                uri = uri_utils.layerUri(layer)
                if uri == qgislayer.source():
                    try:
                        sld = layer.default_style.sld_body.decode()
                        sld = adaptGsToQgs(sld)
                        sldfile = tempFilename("sld")
                        with open(sldfile, 'w') as f:
                            f.write(sld)
                        msg, ok = qgislayer.loadSldStyle(sldfile)
                        if not ok:
                            raise Exception("Could not load style for layer <b>%s</b>" % qgislayer.name())
                        qgislayer.styleChanged.connect(partial(updatePublishedStyle, qgislayer))
                    except Exception as e:
                        setWarning("Could not set style for layer <b>%s</b>" % qgislayer.name())
                    return


_currentMessageBarLayer = None

def _resetCurrentMessageBarLayer():
    global _currentMessageBarLayer
    _currentMessageBarLayer = None

def updatePublishedStyle(layer):
    global _currentMessageBarLayer
    track = pluginSetting("TrackLayers")
    if track and isTrackedLayer(layer):
        if iface.messageBar().currentItem() is None:
            _resetCurrentMessageBarLayer()
        if _currentMessageBarLayer != layer:
            _currentMessageBarLayer = layer
            widget = iface.messageBar().createMessage("",
                    "This layer was uploaded to a geoserver catalog. Do you want to update the published style?")
            updateButton = QtWidgets.QPushButton(widget)
            updateButton.setText("Update")
            def updateStyle():
                url = getTrackingInfo(layer)
                catalog = Catalog(url)
                wrapper = CatalogWrapper(catalog)
                wrapper.publishStyle(layer)
                iface.messageBar().popWidget()
                _resetCurrentMessageBarLayer()
            updateButton.pressed.connect(updateStyle)
            widget.layout().addWidget(updateButton)
            stopTrackingButton = QtWidgets.QPushButton(widget)
            stopTrackingButton.setText("Stop tracking this layer")
            def stopTracking():
                removeTrackedLayer(layer)
                iface.messageBar().popWidget()
                _resetCurrentMessageBarLayer()
            stopTrackingButton.pressed.connect(stopTracking)
            widget.layout().addWidget(stopTrackingButton)
            iface.messageBar().pushWidget(widget, Qgis.Info)
            iface.messageBar().currentItem().geoserverLayer = layer
            #iface.messageBar().widgetRemoved.connect(_resetCurrentMessageBarLayer)


def connectLayerWasAdded(explorer):
    global _explorer
    _explorer = explorer
    QgsProject.instance().layerWasAdded.connect(layerAdded)
    readTrackedLayers()

def disconnectLayerWasAdded():
    QgsProject.instance().layerWasAdded.disconnect(layerAdded)
