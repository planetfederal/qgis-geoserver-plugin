# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
import traceback
from qgis.PyQt import QtCore
from qgis.core import *
from geoserverexplorer.qgis import layers as qgislayers
from geoserverexplorer.qgis.catalog import CatalogWrapper
from geoserverexplorer.gui.confirm import publishLayer
from geoserverexplorer.gui.dialogs.projectdialog import PublishProjectDialog
from geoserver.catalog import ConflictingDataError
from geoserverexplorer.gui.dialogs.layerdialog import PublishLayersDialog
from geoserverexplorer.gui import setInfo, setWarning, setError
from geoserverexplorer.geoserver import GeoserverException

def _publishLayers(catalog, layers, layersUploaded):
    task = PublishLayersTask(catalog, layers) 
    task.taskCompleted.connect(layersUploaded)
    QgsApplication.taskManager().addTask(task)
    QtCore.QCoreApplication.processEvents()

class PublishLayersTask(QgsTask):

    def __init__(self, catalog, layers):
        QgsTask.__init__(self, "Publish layers")
        self.layers = layers
        self.catalog = catalog
        self.exception = None
        self.errortrace = None

    def canCancel(self):
        return False

    def run(self):
        try:
            for layerAndParams in self.layers:
                catalog = CatalogWrapper(self.catalog)
                catalog.publishLayer(*layerAndParams)
            return True
        except Exception as e:            
            self.exception = e
            if isinstance(e, GeoserverException):
                self.errortrace = e.details
            else:
                self.errortrace = traceback.format_exc()
            return False

    def finished(self, ok):
        if ok:
            setInfo("%i layers correctly published" % len(self.layers))
        else:
            setError(str(self.exception), self.errortrace)

def addDraggedLayerToGroup(explorer, layer, groupItem):
    group = groupItem.element
    styles = group.styles
    layers = group.layers
    if layer.name not in layers:
        layers.append(layer.name)
        styles.append(layer.default_style.name)
    group.dirty.update(layers = layers, styles = styles)
    explorer.run(layer.catalog.save,
                 "Update group '" + group.name + "'",
                 [groupItem],
                 group)

def addDraggedUrisToWorkspace(uris, catalog, workspace, explorer, tree):
    if uris and workspace:
        toPublish = []
        allLayers = qgislayers.getAllLayersAsDict()
        publishableLayers = qgislayers.getPublishableLayersAsDict()
        for i, uri in enumerate(uris): 
            layer = None          
            if isinstance(uri, QgsMimeDataUtils.Uri):
                layer = qgislayers.layerFromUri(uri)                
            source = uri if isinstance(uri, str) else uri.uri
            source = source.split("|")[0]
            if layer is None:
                if source in allLayers:
                    layer = publishableLayers.get(source, None)
                else:
                    if isinstance(uri, str):
                        layerName = QtCore.QFileInfo(uri).completeBaseName()
                        layer = QgsRasterLayer(uri, layerName)
                    else:
                        layer = QgsRasterLayer(uri.uri, uri.name)
                    if not layer.isValid() or layer.type() != QgsMapLayer.RasterLayer:
                        if isinstance(uri, str):
                            layerName = QtCore.QFileInfo(uri).completeBaseName()
                            layer = QgsVectorLayer(uri, layerName, "ogr")
                        else:
                            layer = QgsVectorLayer(uri.uri, uri.name, uri.providerKey)
                        if not layer.isValid() or layer.type() != QgsMapLayer.VectorLayer:
                            layer.deleteLater()
                            layer = None
                if layer is None:
                    name = "'%s'" % allLayers[source] if source in allLayers else "with source '%s'" % source
                    msg = "Could not resolve layer " + name
                    QgsMessageLog.logMessage(msg, level=Qgis.Critical)
                else:
                    toPublish.append([layer, workspace])
            else:
                toPublish.append([layer, workspace])

        if toPublish:
            def layersUploaded():
                explorer.resetActivity()
                tree.findAllItems(catalog)[0].refreshContent(explorer)
            _publishLayers(catalog, toPublish, layersUploaded)

def addDraggedStyleToLayer(tree, explorer, styleItem, layerItem):
    catalog = layerItem.element.catalog
    style = styleItem.element
    layer = layerItem.element
    if not hasattr(layer, "default_style") or layer.default_style is None:
        # if default style is missing, make dragged style the layer's default
        # without a default style, some GeoServer operations may fail
        layer.default_style = style
    else:
        # add to layer's additional styles
        styles = layer.styles
        styles.append(style)
        layer.styles = styles
    explorer.run(catalog.save,
             "Add style '" + style.name + "' to layer '" + layer.name + "'",
             [layerItem],
             layer)


def publishProject(tree, explorer, catalog):
    layers = qgislayers.getAllLayers()
    dlg = PublishProjectDialog(catalog)
    dlg.exec_()
    if not dlg.ok:
        return
    workspace = dlg.workspace
    groupName = dlg.groupName
    overwrite = dlg.overwrite
    layersAndParams = [(layer, workspace, overwrite) for layer in layers]

    def layersUploaded():
        groups = qgislayers.getGroups()
        for group in groups:
            names = [layer.name() for layer in groups[group][::-1]]
            try:
                layergroup = catalog.create_layergroup(group, names, names, getGroupBounds(groups[group]))
            except ConflictingDataError:
                layergroup = catalog.get_layergroups(group)[0]
                layergroup.dirty.update(layers = names, styles = names)
            explorer.run(catalog.save, "Create layer group '" + group + "'",
                     [], layergroup)

        if groupName is not None:
            names = [layer.name() for layer in layers[::-1]]
            try:
                layergroup = catalog.create_layergroup(groupName, names, names, getGroupBounds(layers))
            except ConflictingDataError:
                layergroup = catalog.get_layergroups(groupName)[0]
                layergroup.dirty.update(layers = names, styles = names)
            explorer.run(catalog.save, "Create global layer group",
                     [], layergroup)
        tree.findAllItems(catalog)[0].refreshContent(explorer)
        explorer.resetActivity()

    _publishLayers(catalog, layersAndParams, layersUploaded)

def getGroupBounds(layers):
    bounds = None
    def addToBounds(bbox, bounds):
        if bounds is not None:
            bounds = [min(bounds[0], bbox.xMinimum()),
                        max(bounds[1], bbox.xMaximum()),
                        min(bounds[2], bbox.yMinimum()),
                        max(bounds[3], bbox.yMaximum())]
        else:
            bounds = [bbox.xMinimum(), bbox.xMaximum(),
                      bbox.yMinimum(), bbox.yMaximum()]
        return bounds

    for layer in layers:
        transform = QgsCoordinateTransform(layer.crs(), QgsCoordinateReferenceSystem("EPSG:4326"), QgsProject.instance())
        bounds = addToBounds(transform.transformBoundingBox(layer.extent()), bounds)

    return (str(bounds[0]), str(bounds[1]), str(bounds[2]), str(bounds[3]), "EPSG:4326")

def publishLayers(tree, explorer, catalog):
    dlg = PublishLayersDialog(catalog)
    dlg.exec_()
    if dlg.topublish is None:
        return
    layers = [(lay, ws, True, name, style) for lay, ws, name, style in dlg.topublish]
    def layersUploaded():
        catItem = tree.findAllItems(catalog)[0]
        catItem.refreshContent(explorer)
        explorer.resetActivity()
    _publishLayers(catalog, layers, layersUploaded)


