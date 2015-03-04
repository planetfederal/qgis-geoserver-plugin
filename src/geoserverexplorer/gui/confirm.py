'''
Routines to ask for confirmation when performing certain operations
'''
from PyQt4 import QtGui, QtCore
from geoserverexplorer.gui.dialogs.gsnamedialog import getGSLayerName
from geoserverexplorer.gui.gsnameutils import isNameValid, xmlNameRegex

def publishLayer(catalog, layer, workspace=None):
    name = layer.name()
    gslayers = [lyr.name for lyr in catalog.catalog.get_layers()]
    if name in gslayers or not isNameValid(name, gslayers, 0, xmlNameRegex()):
        name = getGSLayerName(name=name, names=gslayers, unique=False)
    catalog.publishLayer(layer, workspace, True, name)


def confirmDelete():
    askConfirmation = bool(QtCore.QSettings().value("/GeoServer/Settings/General/ConfirmDelete", True, bool))
    if not askConfirmation:
        return True
    msg = "You confirm that you want to delete the selected elements?"
    reply = QtGui.QMessageBox.question(None, "Delete confirmation",
                                               msg, QtGui.QMessageBox.Yes |
                                               QtGui.QMessageBox.No, QtGui.QMessageBox.No)
    return reply != QtGui.QMessageBox.No
