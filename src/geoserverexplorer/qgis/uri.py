import urllib
from qgis.core import *
from geoserver.layer import Layer
from geoserverexplorer.geoserver.pki import PKICatalog

def layerUri(layer):
    resource = layer.resource
    catalog = layer.catalog
    def addAuth(_params):
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
                _params['authid'] = catalog.authid
        else:
            _params['PASSWORD'] = catalog.password
            _params['USERNAME'] = catalog.username
    if resource.resource_type == 'featureType':
        params = {
            'SERVICE': 'WFS',
            'VERSION': '1.0.0',
            'REQUEST': 'GetFeature',
            'TYPENAME': resource.workspace.name + ":" + layer.name,
            'SRSNAME': resource.projection,
        }
        addAuth(params)
        uri = layer.catalog.gs_base_url + 'wfs?' + urllib.unquote(urllib.urlencode(params))
    elif resource.resource_type == 'coverage':
        params = {
            'identifier': resource.workspace.name + ":" + resource.name,
            'format': 'GeoTIFF',
            'url': layer.catalog.gs_base_url + 'wcs',
            'cache': 'PreferNetwork'
        }
        addAuth(params)
        uri = urllib.unquote(urllib.urlencode(params))
    else:
        params = {
            'layers': resource.workspace.name + ":" + resource.name,
            'format': 'image/png',
            'url': layer.catalog.gs_base_url + 'wms',
            'styles': '',
            'crs': resource.projection
        }
        addAuth(params)
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

