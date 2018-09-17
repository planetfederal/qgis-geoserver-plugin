# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
from builtins import str
from builtins import object
import os
from qgis.core import *
from qgis.PyQt import QtCore
from geoserverexplorer.geoserver import GeoserverException
from geoserverexplorer.qgis import layers, exporter, utils
from geoserver.catalog import ConflictingDataError, UploadError, FailedRequestError
from geoserverexplorer.qgis.sldadapter import adaptGsToQgs, getGsCompatibleSld, setUnits
from geoserverexplorer.qgis import uri as uri_utils
from geoserverexplorer.geoserver.auth import AuthCatalog
from geoserverexplorer.geoserver.basecatalog import BaseCatalog
from geoserverexplorer.geoserver.util import groupsWithLayer, removeLayerFromGroups, \
    addLayerToGroups
from geoserverexplorer.gui.gsnameutils import xmlNameFixUp, xmlNameIsValid
import requests
from geoserverexplorer.qgis.utils import addTrackedLayer
from qgiscommons2.settings import pluginSetting
from qgiscommons2.files import tempFilename

def createGeoServerCatalog(service_url = "http://localhost:8080/geoserver/rest",
                           username="admin",
                           password="geoserver",
                           authid=None):
    # if not authid use basic auth
    if authid is None:
        catalog = BaseCatalog(service_url, username, password)
    else:
        cache_time = pluginSetting("AuthCatalogXMLCacheTime")
        catalog = AuthCatalog(service_url, authid, cache_time)

    return CatalogWrapper(catalog)


class CatalogWrapper(object):
    '''
    This class is a wrapper for a catalog object, with convenience methods to use it with QGIS layers
    '''

    def __init__(self, catalog):
        self.catalog = catalog

    def clean(self):
        self.cleanUnusedStyles()
        self.cleanUnusedResources()

    def cleanUnusedStyles(self):
        '''cleans styles that are not used by any layer'''
        usedStyles = set()
        styles = self.catalog.get_styles()
        layers = self.catalog.get_layers()
        groups = self.catalog.get_layergroups()
        for layer in layers:
            if layer.default_style is not None:
                usedStyles.add(layer.default_style.name)
            usedStyles.update([s.name for s in layer.styles if s is not None])
        for group in groups:
            usedStyles.update([s for s in group.styles if s is not None])
        toDelete = [s for s in styles if s.name not in usedStyles]
        for style in toDelete:
            try:
                style.catalog.delete(style, purge = True)
            except FailedRequestError:
                QgsMessageLog.logMessage("Cannot delete style '%s'" % style.name)

    def cleanUnusedResources(self):
        '''cleans resources that are not published through any layer in the catalog'''
        usedResources = set()
        resources = self.catalog.get_resources()
        layers = self.catalog.get_layers()
        for layer in layers:
            usedResources.add(layer.resource.name)

        toDelete = [r for r in resources if r.name not in usedResources]
        for resource in toDelete:
            resource.catalog.delete(resource)

        for store in self.catalog.get_stores():
            if len(store.get_resources()) == 0:
                self.catalog.delete(store)

    def consolidateStyles(self):
        '''
        Deletes styles that are redundant and just keeps one copy of them
        in the catalog, configuring the corresponding layers to use that copy
        '''
        used = {}
        allstyles = self.catalog.get_styles()
        for style in allstyles:
            sld = style.sld_body.decode().replace("<sld:Name>%s</sld:Name>" % style.name, "")
            if sld in list(used.keys()):
                used[sld].append(style)
            else:
                used[sld] = [style]

        for sld, styles in used.items():
            if len(styles) == 1:
                continue
            #find the layers that use any of the secondary styles in the list, and make them use the first one
            styleNames = [s.name for s in styles[1:]]
            layers = self.catalog.get_layers()
            for layer in layers:
                changed = False
                if layer.default_style.name in styleNames:
                    layer.default_style = styles[0]
                    changed = True
                alternateStyles = layer.styles
                newAlternateStyles = set()
                for alternateStyle in alternateStyles:
                    if alternateStyle.name in styleNames:
                        newAlternateStyles.add(styles[0])
                    else:
                        newAlternateStyles.add(alternateStyle)
                newAlternateStyles = list(newAlternateStyles)
                if newAlternateStyles != alternateStyles:
                    layer.styles = newAlternateStyles
                    changed = True
                if changed:
                    self.catalog.save(layer)


    def publishStyle(self, layer, overwrite = True, name = None):
        '''
        Publishes the style of a given layer style in the specified catalog. If the overwrite parameter is True,
        it will overwrite a style with that name in case it exists
        '''

        if isinstance(layer, str):
            layer = layers.resolveLayer(layer)
        sld, icons = getGsCompatibleSld(layer)
        if sld is not None:
            name = name if name is not None else layer.name()
            name = name.replace(" ", "_")
            self.uploadIcons(icons)
            self.catalog.create_style(name, sld, overwrite)
        return sld


    def uploadIcons(self, icons):
        for icon in icons:
            url = self.catalog.service_url + "/resource/styles/" + icon[1]
            r = self.catalog.http_request(url, data=icon[2], method="put")


    def getDataFromLayer(self, layer):
        '''
        Returns the data corresponding to a given layer, ready to be passed to the
        method in the Catalog class for uploading to the server.
        If needed, it performs an export to ensure that the file format is supported
        by the upload API to be used for import. In that case, the data returned
        will point to the exported copy of the data, not the original data source
        '''
        if layer.type() == layer.RasterLayer:
            data = exporter.exportRasterLayer(layer)
        else:
            filename = exporter.exportVectorLayer(layer)
            basename, extension = os.path.splitext(filename)
            data = {
                'shp': basename + '.shp',
                'shx': basename + '.shx',
                'dbf': basename + '.dbf',
                'prj': basename + '.prj'
            }
        return data

    def upload(self, layer, workspace=None, overwrite=True, name=None):
        '''uploads the specified layer'''

        if isinstance(layer, str):
            layer = layers.resolveLayer(layer)

        name = name or layer.name()
        title = name
        name = name.replace(" ", "_")

        if layer.type() not in (layer.RasterLayer, layer.VectorLayer):
            raise Exception(layer.name() + ' is not a valid raster or vector layer')

        provider = layer.dataProvider()
        try:
            if layer.type() == layer.RasterLayer:
                path = self.getDataFromLayer(layer)
                self.catalog.create_coveragestore(name,
                                          path=path,
                                          workspace=workspace)
            elif layer.type() == layer.VectorLayer:
                path = self.getDataFromLayer(layer)
                self.catalog.create_featurestore(name,
                                  data=path,
                                  workspace=workspace,
                                  overwrite=overwrite)
        except UploadError as e:
            raise Exception('Could not save the layer %s, there was an upload '
                   'error: %s' % (layer.name()), traceback.format_exc())
        except ConflictingDataError as e:
            # A datastore of this name already exists
            raise GeoserverException('GeoServer reported a conflict creating a store with name %s:'
                     % layer.name(),  traceback.format_exc())


        # Verify the resource was created
        resources = self.catalog.get_resources(name)
        if resources:
            resource = resources[0]
            assert resource.name == name
        else:
            msg = ('could not create layer %s.' % name)
            raise Exception(msg)

        if title != name:
            resource.dirty["title"] = title
            self.catalog.save(resource)
        if resource.latlon_bbox is None:
            box = resource.native_bbox[:4]
            minx, maxx, miny, maxy = [float(a) for a in box]
            if -180 <= minx <= 180 and -180 <= maxx <= 180 and \
                    -90 <= miny <= 90 and -90 <= maxy <= 90:
                resource.latlon_bbox = resource.native_bbox
                resource.projection = "EPSG:4326"
                self.catalog.save(resource)
            else:
                msg = ('Could not set projection for layer '
                       '[%s]. the layer has been created, but its projection should be set manually.')
                raise Exception(msg % layer.name())

    def getConnectionNameFromLayer(self, layer):
        connName = "postgis_store"
        uri = QgsDataSourceURI(layer.dataProvider().dataSourceUri())
        host = uri.host()
        database = uri.database()
        port = uri.port()
        settings = QtCore.QSettings()
        settings.beginGroup(u'/PostgreSQL/connections')
        for name in settings.childGroups():
            settings.beginGroup(name)
            host2 = str(settings.value('host'))
            database2 = str(settings.value('database'))
            port2 = str(settings.value('port'))
            settings.endGroup()
            if port == port2 and database == database2 and host == host2:
                connName = name + "_" + str(uri.schema())
        settings.endGroup()
        return connName


    def publishLayer (self, layer, workspace=None, overwrite=True, name=None, style=None):
        '''
        Publishes a QGIS layer.
        It creates the corresponding store and the layer itself.

        layer: the layer to publish, whether as a QgsMapLayer object or its name in the QGIS TOC.

        workspace: the workspace to publish to. USes the default workspace if not passed
        or None

        name: the name for the published layer. Uses the QGIS layer name if not passed
        or None

        style: the style to use from the ones in the catalog. Will upload the QGIS style if
        not passed or None

        '''

        if isinstance(layer, str):
            layer = layers.resolveLayer(layer)

        addTrackedLayer(layer, self.catalog.service_url)

        name = xmlNameFixUp(name) if name is not None \
            else xmlNameFixUp(layer.name())

        gslayer = self.catalog.get_layer(name)
        if gslayer is not None and not overwrite:
            return

        sld = self.publishStyle(layer, overwrite, name) if style is None else None

        self.upload(layer, workspace, overwrite, name)

        if sld is not None or style is not None:
            #assign style to created store
            publishing = self.catalog.get_layer(name)
            publishing.default_style = style or self.catalog.get_styles(name)[0]
            self.catalog.save(publishing)

    def addLayerToProject(self, name, destName = None):
        '''
        Adds a new layer to the current project based on a layer in a GeoServer catalog
        It will create a new layer with a WFS or WCS connection, pointing to the specified GeoServer
        layer. In the case of a vector layer, it will also fetch its associated style and set it
        as the current style for the created QGIS layer
        '''
        layer = self.catalog.get_layer(name)
        if layer is None:
            raise Exception ("A layer with the name '" + name + "' was not found in the catalog")

        resource = layer.resource
        uri = uri_utils.layerUri(layer)
        QgsNetworkAccessManager.instance().cache().clear()

        if resource.resource_type == "featureType":
            qgslayer = QgsVectorLayer(uri, destName or resource.title, "WFS")
            if not qgslayer.isValid():
                raise Exception ("Layer at %s is not a valid layer" % uri)
            ok = True
            try:
                sld = layer.default_style.sld_body.decode()
                sld = adaptGsToQgs(str(sld))
                sldfile = tempFilename("sld")
                with open(sldfile, 'w') as f:
                    f.write(sld)
                msg, ok = qgslayer.loadSldStyle(sldfile)
            except Exception as e:
                ok = False
            QgsProject.instance().addMapLayers([qgslayer])
            setUnits(qgslayer)
            addTrackedLayer(qgslayer, self.catalog.service_url)
            if not ok:
                raise Exception ("Layer was added, but style could not be set (maybe GeoServer layer is missing default style)")
        elif resource.resource_type == "coverage":
            qgslayer = QgsRasterLayer(uri, destName or resource.title, "wcs" )
            if not qgslayer.isValid():
                raise Exception ("Layer at %s is not a valid layer" % uri)
            QgsProject.instance().addMapLayers([qgslayer])
            addTrackedLayer(qgslayer, self.catalog.service_url)
        elif resource.resource_type == "wmsLayer":
            qgslayer = QgsRasterLayer(uri, destName or resource.title, "wms")
            if not qgslayer.isValid():
                raise Exception ("Layer at %s is not a valid layer" % uri)
            QgsProject.instance().addMapLayers([qgslayer])
            addTrackedLayer(qgslayer, self.catalog.service_url)
        else:
            raise Exception("Cannot add layer. Unsupported layer type.")

    def addGroupToProject(self, name):
        group = self.catalog.get_layergroups(name)[0]
        if group is None:
            raise Exception ("A group with the name '" + name + "' was not found in the catalog")

        uri = uri_utils.groupUri(group)

        qgslayer = QgsRasterLayer(uri, name, "wms")
        if not qgslayer.isValid():
            raise Exception ("Layer at %s is not a valid layer" % uri)
        QgsProject.instance().addMapLayers([qgslayer])


def createPGFeatureStore(catalog, name, workspace=None, overwrite=False,
                        host="localhost", port=5432, database="db", schema="public", user="postgres", passwd=""):
    try:
        store = catalog.get_stores(name, workspace)[0]
    except:
        store = None

    if store is None:
        store = catalog.create_datastore(name, workspace)
        store.connection_parameters.update(
        host=host, port=str(port), database=database, user=user, schema=schema,
        passwd=passwd, dbtype="postgis")
        catalog.save(store)
        return store
    elif overwrite:
        # if existing store is the same we are trying to add, just return it
        params = store.connection_parameters
        if (str(params['port']) == str(port)
            and params['database'] == database
            and params['host'] == host
            and params['user'] == user):
            return store
        else:
            msg = "store named '" + str(name) + "' already exist"
            if workspace is not None:
                msg += " in '" + str(workspace) + "'"
            msg += ' and has different connection parameters.'
            raise ConflictingDataError(msg)
    else:
        return None
