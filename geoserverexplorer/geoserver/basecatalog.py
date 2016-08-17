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

class BaseCatalog(Catalog):

    def __get_layers(self, resource=None):
        """Prefix the layer name with ws name in case of layers with the same name"""
        lyrs = super(BaseCatalog, self).get_layers(resource)
        layers = {}
        for l in lyrs:
            try:
                layers[l.name].append(l)
            except KeyError:
                layers[l.name] = [l]
        lyrs = [l[0] for l in layers.values() if len(l) == 1]
        # Prefix all duplicated names
        for name, ls in layers.items():
            if len(ls) > 1:
                prefixed_names = ["%s:%s" % (r.workspace.name, name) for
                                  r in self.get_resources() if r.name == name]
                i = 0
                for l in ls:
                    l.name = prefixed_names[i]
                    i += 1
                    lyrs.append(l)
        return lyrs


    def get_layer_fqn(self, layer_name):
        """
        Prefix the layer name with the worspace by querying all the resources
        and finding the workspace from the one that matches the layer name.
        If the layer exists in several workspaces, the first match is returned.
        Return layer_name if the layer resource does not exists.
        """
        if layer_name.find(':') != -1:
            return layer_name
        res = [r for r in self.get_resources() if r.name == layer_name]
        try:
            return "%s:%s" % (res[0].workspace.name, layer_name)
        except IndexError:
            return layer_name


    def get_layers(self, resource=None):
        """Prefix the layer name with ws name"""

        def _get_res(name):
            return [r for r in self.get_resources() if r.name == name]

        lyrs = super(BaseCatalog, self).get_layers(resource)
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
                l.name = "%s:%s" % (_get_res(l.name)[0].workspace.name, l.name)
                result.append(l)
            else:
                i = 0
                for l in ls:
                    l.name = self.get_layer_fqn(l.name)
                    i += 1
                    result.append(l)
        return result
