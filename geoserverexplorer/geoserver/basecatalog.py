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
from datetime import datetime, timedelta

__author__ = 'Alessandro Pasotti'
__date__ = 'August 2016'

from geoserver.catalog import Catalog, FailedRequestError
from geoserver.support import url
from geoserver.layer import Layer
from geoserverexplorer import config
from qgis.gui import *
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
        # Original code from gsconfig
        if isinstance(resource, basestring):
            resource = self.get_resource(resource)

        layers_url = url(self.service_url, ["layers.json"])
        response, content = self.http.request(layers_url)
        if response.status == 200:
            lyrs = []
            jsonlayers = json.loads(content)
            if "layer" not in jsonlayers["layers"]: #empty repo
                return []
            for lyr in jsonlayers["layers"]["layer"]:
                lyrs.append(BaseLayer(self, lyr["name"]))
        else:
            raise FailedRequestError("Tried to make a GET request to %s but got a %d status code: \n%s" % (layers_url, response.status, content))

        if resource is not None:
            lyrs = [l for l in lyrs if l.resource.href == resource.href]

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
        for name, ls in layers.items():
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
            config.iface.messageBar().pushMessage("Warning", "Some layers contain non-ascii characters and could not be loaded",
                      level = QgsMessageBar.WARNING,
                      duration = 10)
        return result

    def get_xml(self, rest_url):

        cached_response = self._cache.get(rest_url)

        def is_valid(cached_response):
            return cached_response is not None and datetime.now() - cached_response[0] < timedelta(seconds=5)

        def parse_or_raise(xml):
            try:
                xml = unicode(xml, errors="ignore").decode("utf-8", errors="ignore")
                return XML(xml)
            except (ExpatError, SyntaxError), e:
                msg = "GeoServer gave non-XML response for [GET %s]: %s"
                msg = msg % (rest_url, xml)
                raise Exception(msg, e)

        if is_valid(cached_response):
            raw_text = cached_response[1]
            return parse_or_raise(raw_text)
        else:
            response, content = self.http.request(rest_url)
            if response.status == 200:
                self._cache[rest_url] = (datetime.now(), content)
                return parse_or_raise(content)
            else:
                raise FailedRequestError("Tried to make a GET request to %s but got a %d status code: \n%s" % (rest_url, response.status, content))

