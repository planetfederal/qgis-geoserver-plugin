# -*- coding: utf-8 -*-

"""
***************************************************************************
    A GS config catalog with superpowers
    ---------------------
    Date                 : August 2016
    Copyright            : (C) 2016 Boundless, http://boundlessgeo.com
    Email                : apasotti at boundlessgeo dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""
from builtins import str
from datetime import datetime, timedelta

__author__ = 'Alessandro Pasotti'
__date__ = 'August 2016'

from geoserver.catalog import Catalog, FailedRequestError
from geoserver.support import build_url
from geoserver.layer import Layer
from qgis.gui import *
from qgis.utils import iface
import json
from xml.etree.ElementTree import XML
from xml.parsers.expat import ExpatError

class BaseLayer(Layer):
    """Patched to get correct resources from workspaces"""

    @property
    def resource(self):
        if self.dom is None:
            self.fetch()
        name = self.dom.find("resource/name").text
        if self.name.find(':') != -1:
            return self.catalog.get_resource(name, workspace=self.name.split(':')[0])
        return self.catalog.get_resource(name)


class BaseCatalog(Catalog):

    def layersEndpointUrl(self):
        return self.service_url[:self.service_url.find("/rest")]
        
    def _get_res(self, name):
        return [r for r in self.get_resources() if r.name == name]

    def get_namespaced_name(self, layer_name):
        """
        Prefix the layer name with the workspace by querying all the resources
        and finding the workspace from the one that matches the layer name.
        If the layer exists in several workspaces, the first match is returned.
        Return layer_name if the layer resource does not exists.
        """
        if layer_name.find(':') != -1:
            return layer_name
        res = self._get_res(layer_name)
        try:
            return "%s:%s" % (res[0].workspace.name, layer_name)
        except IndexError:
            return layer_name


    def get_layers(self, resource=None):
        """Prefix the layer name with ws name"""
        lyrs = super().get_layers(resource)
        # Start patch:
        layers = {}
        result = []
        for l in lyrs:
            try:
                layers[l.name].append(l)
            except KeyError:
                layers[l.name] = [l]
        # Prefix all names
        noAscii = False
        for name, ls in list(layers.items()):
            try:
                if len(ls) == 1:
                    l = ls[0]
                    l.name = self.get_namespaced_name(l.name)
                    result.append(l)
                else:
                    i = 0
                    res = self._get_res(ls[0].name)
                    for l in ls:
                        l.name = "%s:%s" % (res[i].workspace.name, l.name)
                        i += 1
                        result.append(l)
            except UnicodeDecodeError:
                noAscii = True

        if noAscii:
            iface.messageBar().pushMessage("Warning", "Some layers contain non-ascii characters and could not be loaded",
                      level = QgsMessageBar.WARNING,
                      duration = 10)
        return result


