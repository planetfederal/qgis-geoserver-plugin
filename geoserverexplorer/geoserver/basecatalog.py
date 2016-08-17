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

__author__ = 'Alessandro Pasotti'
__date__ = 'August 2016'

from geoserver.catalog import Catalog
from geoserver.support import url
from geoserver.layer import Layer

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
        layers_url = url(self.service_url, ["layers.xml"])
        description = self.get_xml(layers_url)
        lyrs = [BaseLayer(self, l.find("name").text) for l in description.findall("layer")]
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
        for name, ls in layers.items():
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
        return result
