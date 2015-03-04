import os
import uuid
import time
from qgis.core import *
from PyQt4 import QtCore, QtGui
from geoserverexplorer.qgis import layers as qgislayers
from geoserverexplorer import config

class UserCanceledOperation(Warning):
    pass

def checkLayers():
    layers = qgislayers.getAllLayers()
    if len(layers) == 0:
        QtGui.QMessageBox.warning(config.iface.mainWindow(), 'QGIS layers needed',
            "No suitable layers can be found in your current QGIS project.\n"
            "You must open the layers in QGIS to be able to work with them.",
            QtGui.QMessageBox.Ok)
        return False
    return True

def tempFolder():
    tempDir = os.path.join(unicode(QtCore.QDir.tempPath()), "geoserverplugin")
    if not QtCore.QDir(tempDir).exists():
        QtCore.QDir().mkpath(tempDir)
    return unicode(os.path.abspath(tempDir))

def tempFilename(ext):
    path = tempFolder()
    ext = "" if ext is None else ext
    filename = path + os.sep + str(time.time())  + "." + ext
    return filename

def tempFilenameInTempFolder(basename):
    '''returns a temporary filename for a given file, putting it into a temp folder but not changing its basename'''
    path = tempFolder()
    folder = os.path.join(path, str(uuid.uuid4()).replace("-",""))
    mkdir(folder)
    filename =  os.path.join(folder, basename)
    return filename

def mkdir(newdir):
    if os.path.isdir(newdir):
        pass
    else:
        head, tail = os.path.split(newdir)
        if head and not os.path.isdir(head):
            mkdir(head)
        if tail:
            os.mkdir(newdir)

def isWindows():
    return os.name == 'nt'


