# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
from qgis.utils import iface
from qgis.core import Qgis, QgsMessageLog

def setInfo(msg):
    iface.messageBar().pushMessage("Info", msg,
                                              level = Qgis.Info,
                                              duration = 10)

def setWarning(msg):
    iface.messageBar().pushMessage("Warning", msg,
                                          level = Qgis.Warning,
                                          duration = 10)

def setError(msg, trace=None):
    iface.messageBar().pushMessage("Geoserver", msg, level=Qgis.Warning, duration=10)
    if trace is not None:
        QgsMessageLog.logMessage("{}:{}".format(msg, trace), level=Qgis.Critical)
