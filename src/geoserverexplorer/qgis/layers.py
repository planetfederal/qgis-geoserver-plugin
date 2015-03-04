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

def getRasterLayers():
    layers = config.iface.legendInterface().layers()
    raster = list()

    for layer in layers:
        if layer.type() == layer.RasterLayer:
            raster.append(layer)
    return raster


def getVectorLayers(shapetype=-1):
    layers = config.iface.legendInterface().layers()
    vector = list()
    for layer in layers:
        if layer.type() == layer.VectorLayer:
            if shapetype == ALL_TYPES or layer.geometryType() == shapetype:
                uri = unicode(layer.source())
                if not uri.lower().endswith("csv") and not uri.lower().endswith("dbf"):
                    vector.append(layer)
    return vector

def getAllLayers():
    layers = []
    layers += getRasterLayers();
    layers += getVectorLayers();
    return layers


def getGroups():
    groups = {}
    rels = config.iface.legendInterface().groupLayerRelationship()
    for rel in rels:
        groupName = rel[0]
        if groupName != '':
            groupLayers = rel[1]
            groups[groupName] = [QgsMapLayerRegistry.instance().mapLayer(layerid) for layerid in groupLayers]
    return groups


