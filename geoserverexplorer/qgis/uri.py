# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#

import urllib.request, urllib.parse, urllib.error
from qgis.core import *
from geoserver.layer import Layer
from geoserver.layergroup import LayerGroup
from geoserverexplorer.geoserver.auth import AuthCatalog


def addAuth(_params, catalog):
    if isinstance(catalog, AuthCatalog):
        _params['authcfg'] = catalog.authid    
    else:
        _params['PASSWORD'] = catalog.password
        _params['USERNAME'] = catalog.username

def layerUri(layer):

    def _get_namespaced_name(ws_name, layer_name):
        """Prefix ws name in case it is not already there"""
        if layer_name.find(':') != -1:
            return layer_name
        return ws_name + ":" + layer_name

    resource = layer.resource
    catalog = layer.catalog
    if resource.resource_type == 'featureType':
        params = {
            'SERVICE': 'WFS',
            'VERSION': '1.0.0',
            'REQUEST': 'GetFeature',
            'TYPENAME': _get_namespaced_name(resource.workspace.name, layer.name),
            'SRSNAME': resource.projection,
        }
        addAuth(params, catalog)
        uri = layer.catalog.layersEndpointUrl() + '/wfs?' + urllib.parse.unquote(urllib.parse.urlencode(params))
    elif resource.resource_type == 'coverage':
        params = {
            'identifier':  _get_namespaced_name(resource.workspace.name, resource.name),
            'format': 'GeoTIFF',
            'url': layer.catalog.layersEndpointUrl() + '/wcs',
            'cache': 'PreferNetwork'
        }
        addAuth(params, catalog)
        uri = urllib.parse.unquote(urllib.parse.urlencode(params))
    else:
        params = {
            'layers': _get_namespaced_name(resource.workspace.name, resource.name),
            'format': 'image/png',
            'url': layer.catalog.layersEndpointUrl() + '/wms',
            'styles': '',
            'crs': resource.projection
        }
        addAuth(params, catalog)
        uri = urllib.parse.unquote(urllib.parse.urlencode(params))

    return uri

def groupUri(group):
    params = {
            'layers': group.name,
            'format': 'image/png',
            'url': group.catalog.layersEndpointUrl() + '/wms',
            'styles': '',
        }
    addAuth(params, group.catalog)
    uri = urllib.parse.unquote(urllib.parse.urlencode(params))
    return uri

def layerMimeUri(element):
    if isinstance(element, Layer):
        layer = element
        uri = layerUri(layer)
        resource = layer.resource
        if resource.resource_type == 'featureType':
            layertype = 'vector'
            provider = 'WFS'
        elif resource.resource_type == 'coverage':
            layertype = 'raster'
            provider = 'wcs'
        else:
            layertype = 'raster'
            provider = 'wms'
        escapedName = resource.title.replace( ":", "\\:" );
        escapedUri = uri.replace( ":", "\\:" );
        mimeUri = ':'.join([layertype, provider, escapedName, escapedUri])
        return mimeUri
    elif isinstance(element, LayerGroup):
        uri = groupUri(element)
        escapedName = resource.title.replace( ":", "\\:" );
        escapedUri = uri.replace( ":", "\\:" );
        mimeUri = ':'.join(["raster", "wms", escapedName, escapedUri])
        return mimeUri
