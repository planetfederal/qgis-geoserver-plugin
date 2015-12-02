from qgis.core import *
from geoserverexplorer import config

ALL_TYPES = -1

class WrongLayerNameException(BaseException) :
    pass

def resolveLayer(name):
    layers = getAllLayers()
    for layer in layers:
        if layer.name() == name:
            return layer
    raise WrongLayerNameException()

def getPublishableLayers():
    layers = config.iface.legendInterface().layers()
    return [layer for layer in layers if layer.dataProvider().name() != "wms"]

def getAllLayers():
    return config.iface.legendInterface().layers()

def getAllLayersAsDict():
    return {layer.source(): layer for layer in getAllLayers()}

def getPublishableLayersAsDict():
    return {layer.source(): layer for layer in getPublishableLayers()}

def getGroups():
    groups = {}
    rels = config.iface.legendInterface().groupLayerRelationship()
    for rel in rels:
        groupName = rel[0]
        if groupName != '':
            groupLayers = rel[1]
            groups[groupName] = [QgsMapLayerRegistry.instance().mapLayer(layerid) for layerid in groupLayers]
    return groups


