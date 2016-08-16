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

    def get_layers(self, resource=None):
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
