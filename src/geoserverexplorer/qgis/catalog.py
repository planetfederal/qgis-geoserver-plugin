# -*- coding: utf-8 -*-

import os
from qgis.core import *
from PyQt4 import QtCore
from geoserverexplorer.qgis import layers, exporter, utils
from geoserver.catalog import ConflictingDataError, UploadError, FailedRequestError
from geoserver.catalog import Catalog as GSCatalog
from geoserverexplorer.qgis.sldadapter import adaptGsToQgs,\
    getGsCompatibleSld
from geoserverexplorer.qgis import uri as uri_utils
from gsimporter.client import Client
from geoserverexplorer.geoserver.pki import PKICatalog, PKIClient
from geoserverexplorer.geoserver.util import groupsWithLayer, removeLayerFromGroups, \
    addLayerToGroups
from geoserverexplorer.gui.gsnameutils import xmlNameFixUp, xmlNameIsValid
import requests

try:
    from processing.modeler.ModelerAlgorithm import ModelerAlgorithm
    from processing.script.ScriptAlgorithm import ScriptAlgorithm
    from processing.core.parameters import *
    from processing.core.outputs import *
    from processing.gui import AlgorithmExecutor
    from processing.gui.SilentProgress import SilentProgress
    from processing.tools.dataobjects import getObjectFromUri as load
    from processing.modeler.ModelerUtils import ModelerUtils
    processingOk = True
except Exception, e:
    processingOk = False

def createGeoServerCatalog(service_url = "http://localhost:8080/geoserver/rest",
                 username="admin", password="geoserver", disable_ssl_certificate_validation=False):
    catalog = GSCatalog(service_url, username, password, disable_ssl_certificate_validation)
    return CatalogWrapper(catalog)


class CatalogWrapper(object):
    '''
    This class is a wrapper for a catalog object, with convenience methods to use it with QGIS layers
    '''

    def __init__(self, catalog):
        self.catalog = catalog
        #we also create a Client object pointing to the same url
        if isinstance(catalog, PKICatalog):
            self.client = PKIClient(catalog.service_url, catalog.key, catalog.cert, catalog.ca_cert)
        else:
            self.client = Client(str(catalog.service_url), catalog.username, catalog.password)


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
            usedStyles.add(layer.default_style.name)
            usedStyles.update([s.name for s in layer.styles if s is not None])
        for group in groups:
            usedStyles.update([s for s in group.styles if s is not None])
        toDelete = [s for s in styles if s.name not in usedStyles]
        for style in toDelete:
            style.catalog.delete(style, purge = True)

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
            sld = style.sld_body.replace("<sld:Name>%s</sld:Name>" % style.name, "")
            if sld in used.keys():
                used[sld].append(style)
            else:
                used[sld] = [style]

        for sld, styles in used.iteritems():
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

        if isinstance(layer, basestring):
            layer = layers.resolveLayer(layer)
        sld, icons = getGsCompatibleSld(layer)
        print sld
        if sld is not None:
            name = name if name is not None else layer.name()
            name = name.replace(" ", "_")
            self.uploadIcons(icons)
            self.catalog.create_style(name, sld, overwrite)
        return sld


    def uploadIcons(self, icons):
        url = self.catalog.gs_base_url + "app/api/icons"
        for icon in icons:
            files = {'file': (icon[1], icon[2])}
            if isinstance(self.catalog, PKICatalog):
                r = requests.post(url, files=files, cert=(self.catalog.cert, self.catalog.key), verify=self.catalog.ca_cert)
            else:
                r = requests.post(url, files=files, auth=(self.catalog.username, self.catalog.password))
            try:
                r.raise_for_status()
            except Exception, e:
                raise Exception ("Error uploading SVG icon to GeoServer:\n" + str(e))
            break


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


    def _publishPostgisLayer(self, layer, workspace, overwrite, name, storename=None):
        uri = QgsDataSourceURI(layer.dataProvider().dataSourceUri())

        # check for table.name conflict in existing layer names where the
        # table.name is not the same as the user-chosen layer name,
        # i.e. unintended overwrite
        resource = self.catalog.get_resource(uri.table())
        if resource is not None and uri.table() != name:
            raise Exception("QGIS PostGIS layer has table name conflict with "
                            "existing GeoServer layer name: {0}\n"
                            "You may need to rename GeoServer layer name."
                            .format(uri.table()))

        conname = self.getConnectionNameFromLayer(layer)
        storename = xmlNameFixUp(storename or conname)

        if not xmlNameIsValid(storename):
            raise Exception("Database connection name is invalid XML and can "
                            "not be auto-fixed: {0} -> {1}"
                            .format(conname, storename))

        if not uri.username():
            raise Exception("GeoServer requires database connection's username "
                            "to be defined")

        store = createPGFeatureStore(self.catalog,
                                     storename,
                                     workspace = workspace,
                                     overwrite = overwrite,
                                     host = uri.host(),
                                     database = uri.database(),
                                     schema = uri.schema(),
                                     port = uri.port(),
                                     user = uri.username(),
                                     passwd = uri.password())
        if store is not None:
            rscname = name if uri.table() != name else uri.table()
            grpswlyr = []
            if overwrite:
                # TODO: How do we honor *unchecked* user setting of
                #   "Delete resource when deleting layer" here?
                #   Is it an issue, if overwrite is expected?

                # We will soon have two layers with slightly different names,
                # a temp based upon table.name, the other possibly existing
                # layer with the same custom name, which may belong to group(s).
                # If so, remove existing layer from any layer group, before
                # continuing on with layer delete and renaming of new feature
                # type layer to custom name, then add new resultant layer back
                # to any layer groups the existing layer belonged to. Phew!

                flyr = self.catalog.get_layer(rscname)
                if flyr is not None:
                    grpswlyr = groupsWithLayer(self.catalog, flyr)
                    if grpswlyr:
                        removeLayerFromGroups(self.catalog, flyr, grpswlyr)
                    self.catalog.delete(flyr)
                # TODO: What about when the layer name is the same, but the
                #   underlying db connection/store has changed? Not an issue?
                #   The layer is deleted, which is correct, but the original
                #   db store and feature type will not be changed. A conflict?
                frsc = store.get_resources(name=rscname)
                if frsc is not None:
                    self.catalog.delete(frsc)

            # for dbs the name has to be the table name, initially
            ftype = self.catalog.publish_featuretype(uri.table(), store,
                                                     layer.crs().authid())

            # once table-based feature type created, switch name to user-chosen
            if ftype.name != rscname:
                ftype.dirty["name"] = rscname
            self.catalog.save(ftype)

            # now re-add to any previously assigned-to layer groups
            if overwrite and grpswlyr:
                ftype = self.catalog.get_resource(rscname)
                if ftype:
                    addLayerToGroups(self.catalog, ftype, grpswlyr,
                                     workspace=workspace)


    def _uploadRest(self, layer, workspace, overwrite, name):
        if layer.type() == layer.RasterLayer:
            path = self.getDataFromLayer(layer)
            self.catalog.create_coveragestore(name,
                                      path,
                                      workspace=workspace,
                                      overwrite=overwrite)
        elif layer.type() == layer.VectorLayer:
            path = self.getDataFromLayer(layer)
            self.catalog.create_featurestore(name,
                              path,
                              workspace=workspace,
                              overwrite=overwrite)


    def _uploadImporter(self, layer, workspace, overwrite, name):
        # @todo - more richness needed to allow ingestion into target store
        # versus just publishing the layer to a workspace as a shapefile
        path = self.getDataFromLayer(layer)
        if isinstance(path, dict):
            if 'shp' in path:
                path = path['shp']
            else:
                raise Exception('Unexpected condition : %s', path.keys())
        session = self.client.upload(path)
        if not session.tasks:
            raise Exception('Geoserver is not able to process the uploaded data')
        if len(session.tasks) != 1:
            # this probably shouldn't happen but just in case
            raise Exception('Unexpected condition')
        # set workspace if needed (network trip)
        # limitation in setting name as importer interprets this as a request
        # to use an existing store by name
        if workspace:
            session.tasks[0].set_target(workspace=workspace.name)
        if overwrite:
            session.tasks[0].set_update_mode('REPLACE')
        session.commit()


    def upload(self, layer, workspace=None, overwrite=True, name=None):
        '''uploads the specified layer'''

        if isinstance(layer, basestring):
            layer = layers.resolveLayer(layer)

        name = name if name is not None else layer.name()
        title = name
        name = name.replace(" ", "_")

        settings = QtCore.QSettings()
        restApi = bool(settings.value("/GeoServer/Settings/GeoServer/UseRestApi", True, bool))

        if layer.type() not in (layer.RasterLayer, layer.VectorLayer):
            msg = layer.name() + ' is not a valid raster or vector layer'
            raise Exception(msg)

        provider = layer.dataProvider()
        try:
            if provider.name() == 'postgres':
                self._publishPostgisLayer(layer, workspace, overwrite, name)
            elif restApi:
                self._uploadRest(layer, workspace, overwrite, name)
            else:
                self._uploadImporter(layer, workspace, overwrite, name)
        except UploadError, e:
            msg = ('Could not save the layer %s, there was an upload '
                   'error: %s' % (layer.name(), str(e)))
            e.args = (msg,)
            raise
        except ConflictingDataError, e:
            # A datastore of this name already exists
            msg = ('GeoServer reported a conflict creating a store with name %s: '
                   '"%s". This should never happen because a brand new name '
                   'should have been generated. But since it happened, '
                   'try renaming the file or deleting the store in '
                   'GeoServer.' % (layer.name(), str(e)))
            e.args = (msg,)
            raise e


        # Verify the resource was created
        resource = self.catalog.get_resource(name)
        if resource is not None:
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

    def publishGroup(self, name, destName = None, workspace = None, overwrite = False, overwriteLayers = False):

        '''
        Publishes a group in the given catalog

        name: the name of the QGIS group to publish. It will also be used as the GeoServer layergroup name

        workspace: The workspace to add the group to

        overwrite: if True, it will overwrite a previous group with the specified name, if it exists

        overwriteLayers: if False, in case a layer in the group is not found in the specified workspace, the corresponding layer
        from the current QGIS project will be published, but all layers of the group that can be found in the GeoServer
        workspace will not be published. If True, all layers in the group are published, even if layers with the same name
        exist in the workspace
        '''

        groups = layers.getGroups()
        if name not in groups:
            raise Exception("The specified group does not exist")

        destName = destName if destName is not None else name
        gsgroup = self.catalog.get_layergroup(destName)
        if gsgroup is not None and not overwrite:
            return


        group = groups[name]

        for layer in group:
            gslayer = self.catalog.get_layer(layer.name())
            if gslayer is None or overwriteLayers:
                self.publishLayer(layer, workspace, True)

        names = [layer.name() for layer in group]

        layergroup = self.catalog.create_layergroup(destName, names, names)
        self.catalog.save(layergroup)

    def publishLayer (self, layer, workspace=None, overwrite=True, name=None):
        '''
        Publishes a QGIS layer.
        It creates the corresponding store and the layer itself.
        If a pre-upload hook is set, its runs it and publishes the resulting layer

        layer: the layer to publish, whether as a QgsMapLayer object or its name in the QGIS TOC.

        workspace: the workspace to publish to. USes the default workspace if not passed
        or None

        name: the name for the published layer. Uses the QGIS layer name if not passed
        or None

        '''

        if isinstance(layer, basestring):
            layer = layers.resolveLayer(layer)

        name = xmlNameFixUp(name) if name is not None \
            else xmlNameFixUp(layer.name())

        gslayer = self.catalog.get_layer(name)
        if gslayer is not None and not overwrite:
            return

        title = name

        sld = self.publishStyle(layer, overwrite, name)

        layer = self.preprocess(layer)
        self.upload(layer, workspace, overwrite, title)

        if sld is not None:
            #assign style to created store
            publishing = self.catalog.get_layer(name)
            publishing.default_style = self.catalog.get_style(name)
            self.catalog.save(publishing)

    def preprocess(self, layer):
        '''
        Preprocesses the layer with the corresponding preprocess hook and returns the path to the
        resulting layer. If no preprocessing is performed, it returns the input layer itself
        '''
        if not processingOk:
            return layer

        if layer.type() == layer.RasterLayer:
            try:
                hookFile = str(QtCore.QSettings().value("/GeoServer/Settings/GeoServer/PreuploadRasterHook", ""))
                alg = self.getAlgorithmFromHookFile(hookFile)
                if (len(alg.parameters) == 1 and isinstance(alg.parameters[0], ParameterRaster)
                    and len(alg.outputs) == 1 and isinstance(alg.outputs[0], OutputRaster)):
                    alg.parameters[0].setValue(layer)
                    if runalg(alg, SilentProgress()):
                        return load(alg.outputs[0].value)
                    return layer
            except:
                return layer
        elif layer.type() == layer.VectorLayer:
            try:
                hookFile = str(QtCore.QSettings().value("/GeoServer/Settings/GeoServer/PreuploadVectorHook", ""))
                alg = self.getAlgorithmFromHookFile(hookFile)
                if (len(alg.parameters) == 1 and isinstance(alg.parameters[0], ParameterVector)
                    and len(alg.outputs) == 1 and isinstance(alg.outputs[0], OutputVector)):
                    alg.parameters[0].setValue(layer)
                    if runalg(alg, SilentProgress()):
                        return load(alg.outputs[0].value)
                    return layer
            except:
                return layer

    def getAlgorithmFromHookFile(self, hookFile):
        if hookFile.endswith('py'):
            script = ScriptAlgorithm(hookFile)
            script.provider = Providers.providers['script']
            return script
        elif hookFile.endswith('model'):
            model = ModelerAlgorithm()
            model.openModel(hookFile)
            model.provider = Providers.providers['model']
            return model
        else:
            raise Exception ("Wrong hook file")

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

        if resource.resource_type == "featureType":
            qgslayer = QgsVectorLayer(uri, destName or resource.title, "WFS")
            if not qgslayer.isValid():
                raise Exception ("Layer at %s is not a valid layer" % uri)
            ok = True
            try:
                sld = layer.default_style.sld_body
                sld = adaptGsToQgs(sld)
                sldfile = utils.tempFilename("sld")
                with open(sldfile, 'w') as f:
                    f.write(sld)
                msg, ok = qgslayer.loadSldStyle(sldfile)
            except Exception, e:
                ok = False
            QgsMapLayerRegistry.instance().addMapLayers([qgslayer])
            if not ok:
                raise Exception ("Layer was added, but style could not be set (maybe GeoServer layer is missing default style)")
        elif resource.resource_type == "coverage":
            qgslayer = QgsRasterLayer(uri, destName or resource.title, "wcs" )
            if not qgslayer.isValid():
                raise Exception ("Layer at %s is not a valid layer" % uri)
            QgsMapLayerRegistry.instance().addMapLayers([qgslayer])
        elif resource.resource_type == "wmsLayer":
            qgslayer = QgsRasterLayer(uri, destName or resource.title, "wms")
            if not qgslayer.isValid():
                raise Exception ("Layer at %s is not a valid layer" % uri)
            QgsMapLayerRegistry.instance().addMapLayers([qgslayer])
        else:
            raise Exception("Cannot add layer. Unsupported layer type.")

def createPGFeatureStore(catalog, name, workspace=None, overwrite=False,
    host="localhost", port=5432, database="db", schema="public", user="postgres", passwd=""):
    try:
        store = catalog.get_store(name, workspace)
    except FailedRequestError:
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


