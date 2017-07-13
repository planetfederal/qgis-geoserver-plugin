# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
import os
import uuid
import time
from qgis.core import *
from qgis.utils import *
from PyQt4 import QtCore, QtGui
from geoserverexplorer.qgis import layers as qgislayers
from geoserverexplorer.qgis import uri as uri_utils
import json

class UserCanceledOperation(Warning):
    pass

def checkLayers():
    layers = qgislayers.getAllLayers()
    if len(layers) == 0:
        QtGui.QMessageBox.warning(iface.mainWindow(), 'QGIS layers needed',
            "No suitable layers can be found in your current QGIS project.\n"
            "You must open the layers in QGIS to be able to work with them.",
            QtGui.QMessageBox.Ok)
        return False
    return True


def userFolder():
    folder = os.path.join(QgsApplication.qgisSettingsDirPath(), 'geoserver')
    try:
        os.mkdir(folder)
    except OSError:
        pass


def isWindows():
    return os.name == 'nt'

tracked = []

def formatSource(source):
    if isinstance(source, QgsRasterLayer):
        return None
    if isinstance(source, QgsVectorLayer):
        source = source.source()
    source = os.path.normcase(source)

def addTrackedLayer(layer, catalogUrl):
    global tracked
    source = formatSource(layer.source())
    if getTrackingInfo(layer) is None:
        tracked.append([source, catalogUrl])
        saveTrackedLayers()

def removeTrackedLayer(layer):
    global tracked
    source = formatSource(layer.source())
    for i, s in enumerate(tracked):
        if s[0] == source:
            del tracked[i]
            saveTrackedLayers()
            return

def saveTrackedLayers():
    filename = os.path.join(userFolder(), "trackedlayers")
    with open(filename, "w") as f:
        f.write(json.dumps(tracked))

def readTrackedLayers():
    try:
        global tracked
        filename = os.path.join(userFolder(), "trackedlayers")
        if os.path.exists(filename):
            with open(filename) as f:
                tracked = json.load(f)
    except:
        pass

def isTrackedLayer(layer):
    return (formatSource(layer.source()) in [t[0] for t in tracked])

def getTrackingInfo(layer):
    source = formatSource(layer.source())
    for obj in tracked:
        if obj[0] == source:
            return obj[1]
