# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
import urllib
from qgis.core import *
from geoserver.layer import Layer
from geoserverexplorer.geoserver.pki import PKICatalog
from geoserver.layergroup import LayerGroup


def addAuth(_params, catalog):
    if hasattr(catalog, 'authid') and catalog.authid is not None:
        hasauthcfg = False
        try:
            configpki = QgsAuthConfigPkiPaths()
            if not hasattr(configpki, "issuerAsPem"):
                # issuerAsPem() removed at same time as authcfg introduced
                #   in core PKI implementation
                hasauthcfg = True
        except:
            pass
        if hasauthcfg and QGis.QGIS_VERSION_INT >= 20801:
            _params['authcfg'] = catalog.authid
        else:
            if QGis.QGIS_VERSION_INT >= 21200:
                _params['authcfg'] = catalog.authid
            else:
                _params['authid'] = catalog.authid
    elif hasattr(catalog, 'authcfg') and catalog.authcfg is not None:
        _params['authcfg'] = catalog.authcfg
    else:
        _params['PASSWORD'] = catalog.password
        _params['USERNAME'] = catalog.username

def layerUri(layer):
    resource = layer.resource
    catalog = layer.catalog
    if resource.resource_type == 'featureType':
        params = {
            'SERVICE': 'WFS',
            'VERSION': '1.0.0',
            'REQUEST': 'GetFeature',
            'TYPENAME': resource.workspace.name + ":" + layer.name,
            'SRSNAME': resource.projection,
        }
        addAuth(params, catalog)
        uri = layer.catalog.gs_base_url + 'wfs?' + urllib.unquote(urllib.urlencode(params))
    elif resource.resource_type == 'coverage':
        params = {
            'identifier': resource.workspace.name + ":" + resource.name,
            'format': 'GeoTIFF',
            'url': layer.catalog.gs_base_url + 'wcs',
            'cache': 'PreferNetwork'
        }
        addAuth(params, catalog)
        uri = urllib.unquote(urllib.urlencode(params))
    else:
        params = {
            'layers': resource.workspace.name + ":" + resource.name,
            'format': 'image/png',
            'url': layer.catalog.gs_base_url + 'wms',
            'styles': '',
            'crs': resource.projection
        }
        addAuth(params, catalog)
        uri = urllib.unquote(urllib.urlencode(params))

    return uri

def groupUri(group):
    params = {
            'layers': group.name,
            'format': 'image/png',
            'url': group.catalog.gs_base_url + 'wms',
            'styles': '',
        }
    addAuth(params, group.catalog)
    uri = urllib.unquote(urllib.urlencode(params))
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
