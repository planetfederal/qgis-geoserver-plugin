from PyQt4 import QtCore
from qgis.core import *
from geoserverexplorer.qgis import layers as qgislayers
from geoserverexplorer.qgis.catalog import CatalogWrapper
from geoserverexplorer.gui.confirm import publishLayer
from geoserverexplorer.gui.dialogs.projectdialog import PublishProjectDialog
from geoserver.catalog import ConflictingDataError
from geoserverexplorer.gui.dialogs.layerdialog import PublishLayersDialog

def publishDraggedGroup(explorer, groupItem, catalog, workspace):
    groupName = groupItem.element
    groups = qgislayers.getGroups()
    group = groups[groupName]
    gslayers= [layer.name for layer in catalog.get_layers()]
    missing = []
    overwrite = bool(QtCore.QSettings().value("/GeoServer/Settings/GeoServer/OverwriteGroupLayers", True, bool))
    for layer in group:
        if layer.name() not in gslayers or overwrite:
            missing.append(layer)
    if missing:
        explorer.setProgressMaximum(len(missing), "Publish layers")
        progress = 0
        cat = CatalogWrapper(catalog)
        for layer in missing:
            explorer.setProgress(progress)
            explorer.run(cat.publishLayer,
                     None,
                     [],
                     layer, workspace, True)
            progress += 1
            explorer.setProgress(progress)
        explorer.resetActivity()
    names = [layer.name() for layer in group]
    layergroup = catalog.create_layergroup(groupName, names, names)
    explorer.run(catalog.save, "Create layer group from group '" + groupName + "'",
             [], layergroup)

def publishDraggedLayer(explorer, layer, workspace):
    cat = workspace.catalog
    cat = CatalogWrapper(cat)
    ret = explorer.run(publishLayer,
             "Publish layer from layer '" + layer.name() + "'",
             [],
             cat, layer, workspace)
    return ret

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

def addDraggedUrisToWorkspace(uris, catalog, workspace, tree):
    if uris:
        if len(uris) > 1:
            explorer.setProgressMaximum(len(uris))
        for i, uri in enumerate(uris):
            if isinstance(uri, basestring):
                layerName = QtCore.QFileInfo(uri).completeBaseName()
                layer = QgsRasterLayer(uri, layerName)
            else:
                layer = QgsRasterLayer(uri.uri, uri.name)
            if not layer.isValid() or layer.type() != QgsMapLayer.RasterLayer:
                if isinstance(uri, basestring):
                    layerName = QtCore.QFileInfo(uri).completeBaseName()
                    layer = QgsVectorLayer(uri, layerName, "ogr")
                else:
                    layer = QgsVectorLayer(uri.uri, uri.name, uri.providerKey)
                if not layer.isValid() or layer.type() != QgsMapLayer.VectorLayer:
                    layer.deleteLater()
                    name = uri if isinstance(uri, basestring) else uri.uri
                    explorer.setError("Error reading file {} or it is not a valid layer file".format(name))
                else:
                    if not publishDraggedLayer(explorer, layer, workspace):
                        return []
            else:
                if not publishDraggedLayer(explorer, layer, workspace):
                    return []
            setProgress(i + 1)
        resetActivity()
        return [tree.findAllItems(catalog)[0]]
    else:
        return []

def addDraggedStyleToLayer(tree, explorer, styleItem, layerItem):
    catalog = layerItem.element.catalog
    catItem = tree.findFirstItem(catalog)
    style = styleItem.element
    layer = layerItem.element
    if layer.default_style is None:
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
             [catItem],
             layer)


def publishProject(tree, explorer, catalog):
    layers = qgislayers.getAllLayers()
    dlg = PublishProjectDialog(catalog)
    dlg.exec_()
    if not dlg.ok:
        return
    workspace = dlg.workspace
    groupName = dlg.groupName
    explorer.setProgressMaximum(len(layers), "Publish layers")
    progress = 0
    cat = CatalogWrapper(catalog)
    for layer in layers:
        explorer.setProgress(progress)
        explorer.run(publishLayer,
                     None,
                     [],
                     cat, layer, workspace)
        progress += 1
        explorer.setProgress(progress)
    explorer.resetActivity()
    groups = qgislayers.getGroups()
    for group in groups:
        names = [layer.name() for layer in groups[group]]
        try:
            layergroup = catalog.create_layergroup(group, names, names)
            explorer.run(catalog.save, "Create layer group '" + group + "'",
                 [], layergroup)
        except ConflictingDataError, e:
            explorer.setWarning(str(e))

    if groupName is not None:
        names = [layer.name() for layer in layers]
        layergroup = catalog.create_layergroup(groupName, names, names)
        explorer.run(catalog.save, "Create global layer group",
                 [], layergroup)
    tree.findAllItems(catalog)[0].refreshContent(explorer)
    explorer.resetActivity()

def publishLayers(tree, explorer, catalog):
    dlg = PublishLayersDialog(catalog)
    dlg.exec_()
    if dlg.topublish is None:
        return
    cat = CatalogWrapper(catalog)
    progress = 0
    explorer.setProgressMaximum(len(dlg.topublish), "Publish layers")
    for layer, workspace, name in dlg.topublish:
        explorer.run(cat.publishLayer,
             None,
             [],
             layer, workspace, True, name)
        progress += 1
        explorer.setProgress(progress)
    catItem = tree.findAllItems(catalog)[0]
    catItem.refreshContent(explorer)
    explorer.resetActivity()
