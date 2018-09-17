# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
from qgis.core import *

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
    layers = getAllLayers()
    return [layer for layer in layers if layer.dataProvider().name() != "wms"]

def getAllLayers():
    return list(QgsProject.instance().mapLayers().values())

def getAllLayersAsDict():
    return {layer.source(): layer for layer in getAllLayers()}

def getPublishableLayersAsDict():
    return {layer.source(): layer for layer in getPublishableLayers()}

def getGroups():
    groups = {}
    root = QgsProject.instance().layerTreeRoot()
    for child in root.children():
        if isinstance(child, QgsLayerTreeGroup):
            layers = []
            for subchild in child.children():
                if isinstance(subchild, QgsLayerTreeLayer):
                    layers.append(subchild.layer())
            groups[child.name()] = layers

    return groups

def layerFromUri(uri):
    allLayers = getAllLayers()
    source = uri.uri.split("|")[0]
    for layer in getAllLayers():
        if layer.source() == source and layer.name() == uri.name:
            return layer

