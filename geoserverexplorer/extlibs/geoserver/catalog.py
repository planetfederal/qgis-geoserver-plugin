# -*- coding: utf-8 -*-
'''
gsconfig is a python library for manipulating GeoServer via the GeoServer RESTConfig API

The project is distributed under a MIT License .
'''

from datetime import datetime, timedelta
import logging
from geoserver.layer import Layer
from geoserver.resource import FeatureType, Coverage
from geoserver.store import (coveragestore_from_index, datastore_from_index,
                             wmsstore_from_index, UnsavedDataStore,
                             UnsavedCoverageStore, UnsavedWmsStore)
from geoserver.style import Style
from geoserver.support import prepare_upload_bundle, build_url, JDBCVirtualTable
from geoserver.layergroup import LayerGroup, UnsavedLayerGroup
from geoserver.workspace import workspace_from_index, Workspace
import os
from xml.etree.ElementTree import XML
from xml.parsers.expat import ExpatError
import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

try:
    from past.builtins import basestring
except ImportError:
    pass

try:
    from urllib.parse import urlparse, urlencode, parse_qsl
except ImportError:
    from urlparse import urlparse, parse_qsl
    from urllib import urlencode


logger = logging.getLogger("gsconfig.catalog")


class UploadError(Exception):
    pass


class ConflictingDataError(Exception):
    pass


class AmbiguousRequestError(Exception):
    pass


class FailedRequestError(Exception):
    pass


def _name(named):
    """Get the name out of an object.  This varies based on the type of the input:
       * the "name" of a string is itself
       * the "name" of None is itself
       * the "name" of an object with a property named name is that property -
         as long as it's a string
       * otherwise, we raise a ValueError
    """
    if isinstance(named, basestring) or named is None:
        return named
    elif hasattr(named, 'name') and isinstance(named.name, basestring):
        return named.name
    else:
        raise ValueError("Can't interpret %s as a name or a configuration object" % named)


class Catalog(object):
    """
    The GeoServer catalog represents all of the information in the GeoServer
    configuration.    This includes:
    - Stores of geospatial data
    - Resources, or individual coherent datasets within stores
    - Styles for resources
    - Layers, which combine styles with resources to create a visible map layer
    - LayerGroups, which alias one or more layers for convenience
    - Workspaces, which provide logical grouping of Stores
    - Maps, which provide a set of OWS services with a subset of the server's
        Layers
    - Namespaces, which provide unique identifiers for resources
    """

    def __init__(self, service_url, username="admin", password="geoserver", validate_ssl_certificate=True, access_token=None):
        self.service_url = service_url.strip("/")
        self.username = username
        self.password = password
        self.validate_ssl_certificate = validate_ssl_certificate
        self.access_token = access_token
        self.setup_connection()

        self._cache = {}
        self._version = None

    def __getstate__(self):
        '''http connection cannot be pickled'''
        state = dict(vars(self))
        state.pop('http', None)
        state['http'] = None
        return state

    def __setstate__(self, state):
        '''restore http connection upon unpickling'''
        self.__dict__.update(state)
        self.setup_connection()

    def setup_connection(self):
        self.client = requests.session()
        self.client.verify = self.validate_ssl_certificate
        parsed_url = urlparse(self.service_url)
        retry = Retry(
            total = 6,
            status = 6,
            backoff_factor = 0.9,
            status_forcelist = [502, 503, 504],
            method_whitelist = set(['HEAD', 'TRACE', 'GET', 'PUT', 'POST', 'OPTIONS', 'DELETE'])
        )

        self.client.mount("{}://".format(parsed_url.scheme), HTTPAdapter(max_retries=retry))

    def http_request(self, url, data=None, method='get', headers = {}):
        req_method = getattr(self.client, method.lower())

        if self.access_token:
            headers['Authorization'] = "Bearer {}".format(self.access_token)
            parsed_url = urlparse(url)
            params = parse_qsl(parsed_url.query.strip())
            params.append(('access_token', self.access_token))
            params = urlencode(params)
            url = "{proto}://{address}{path}?{params}".format(proto=parsed_url.scheme, address=parsed_url.netloc,
                                                              path=parsed_url.path, params=params)

            resp = req_method(url, headers=headers, data=data)
        else:
            resp = req_method(url, headers=headers, data=data, auth=(self.username, self.password))
        return resp

    def about(self):
        '''return the about information as a formatted html'''
        about_url = self.service_url + "/about/version.html"
        response = self.http_request(about_url)
        if response.status_code == 200:
            return response.text
        raise FailedRequestError('Unable to determine version: %s' %
                                 (content or response.status))

    def gsversion(self):
        '''obtain the version or just 2.2.x if < 2.3.x
        Raises:
            FailedRequestError: If the request fails.
        '''
        if self._version:
            return self._version
        url = "{}/about/version.xml".format(self.service_url)
        resp = self.http_request(url)
        version = None
        if resp.status_code == 200:
            dom = XML(resp.content)
            resources = dom.findall("resource")
            for resource in resources:
                if resource.attrib["name"] == "GeoServer":
                    try:
                        version = resource.find("Version").text
                        break
                    except:
                        pass

        # This will raise an exception if the catalog is not available
        # If the catalog is available but could not return version information,
        # it is an old version that does not support that
        if version is None:
            # just to inform that version < 2.3.x
            version = "2.2.x"
        self._version = version
        return version

    def delete(self, config_object, purge=None, recurse=False):
        """
        send a delete request
        XXX [more here]
        """
        rest_url = config_object.href
        params = []

        # purge deletes the SLD from disk when a style is deleted
        if purge:
            params.append("purge=" + str(purge))

        # recurse deletes the resource when a layer is deleted.
        if recurse:
            params.append("recurse=true")

        if params:
            rest_url = rest_url + "?" + "&".join(params)

        headers = {
            "Content-type": "application/xml",
            "Accept": "application/xml"
        }

        resp = self.http_request(rest_url, method='delete', headers=headers)
        if resp.status_code != 200:
            raise FailedRequestError('Failed to make DELETE request: {}, {}'.format(resp.status_code, resp.text))

        self._cache.clear()

        # do we really need to return anything other than None?
        return (resp)

    def get_xml(self, rest_url):
        cached_response = self._cache.get(rest_url)

        def is_valid(cached_response):
            return cached_response is not None and datetime.now() - cached_response[0] < timedelta(seconds=5)

        def parse_or_raise(xml):
            try:
                return XML(xml)
            except (ExpatError, SyntaxError) as e:
                msg = "GeoServer gave non-XML response for [GET %s]: %s"
                msg = msg % (rest_url, xml)
                raise Exception(msg, e)

        if is_valid(cached_response):
            raw_text = cached_response[1]
            return parse_or_raise(raw_text)
        else:
            resp = self.http_request(rest_url)
            if resp.status_code == 200:
                self._cache[rest_url] = (datetime.now(), resp.content)
                return parse_or_raise(resp.content)
            else:
                raise FailedRequestError(resp.content)

    def reload(self):
        url = "{}/reload".format(self.service_url)
        resp = self.http_request(url, method='post')
        self._cache.clear()
        return resp

    def reset(self):
        url = "{}/reset".format(self.service_url)
        resp = self.http_request(url, method='post')
        self._cache.clear()
        return resp

    def save(self, obj, content_type="application/xml"):
        """
        saves an object to the REST service
        gets the object's REST location and the data from the object,
        then POSTS the request.
        """
        rest_url = obj.href
        data = obj.message()

        headers = {
            "Content-type": content_type,
            "Accept": content_type
        }

        logger.debug("{} {}".format(obj.save_method, obj.href))
        resp = self.http_request(rest_url, method=obj.save_method.lower(), data=data, headers=headers)

        if resp.status_code not in (200, 201):
            raise FailedRequestError('Failed to save to Geoserver catalog: {}, {}'.format(resp.status_code, resp.text))

        self._cache.clear()
        return resp

    def get_stores(self, names=None, workspaces=None):
        '''
          Returns a list of stores in the catalog. If workspaces is specified will only return stores in those workspaces.
          If names is specified, will only return stores that match.
          names can either be a comma delimited string or an array.
          Will return an empty list if no stores are found.
        '''

        if isinstance(workspaces, Workspace):
            workspaces = [workspaces]
        elif isinstance(workspaces, list) and [w for w in workspaces if isinstance(w, Workspace)]:
            # nothing
            pass
        else:
            workspaces = self.get_workspaces(names=workspaces)

        stores = []
        for ws in workspaces:
            ds_list = self.get_xml(ws.datastore_url)
            cs_list = self.get_xml(ws.coveragestore_url)
            wms_list = self.get_xml(ws.wmsstore_url)
            stores.extend([datastore_from_index(self, ws, n) for n in ds_list.findall("dataStore")])
            stores.extend([coveragestore_from_index(self, ws, n) for n in cs_list.findall("coverageStore")])
            stores.extend([wmsstore_from_index(self, ws, n) for n in wms_list.findall("wmsStore")])

        if names is None:
            names = []
        elif isinstance(names, basestring):
            names = [s.strip() for s in names.split(',') if s.strip()]

        if stores and names:
            return ([store for store in stores if store.name in names])

        return stores

    def create_datastore(self, name, workspace=None):
        if isinstance(workspace, basestring):
            workspace = self.get_workspaces(names=workspace)[0]
        elif workspace is None:
            workspace = self.get_default_workspace()
        return UnsavedDataStore(self, name, workspace)

    def create_wmsstore(self, name, workspace = None, user = None, password = None):
        if workspace is None:
            workspace = self.get_default_workspace()
        return UnsavedWmsStore(self, name, workspace, user, password)

    def create_wmslayer(self, workspace, store, name, nativeName=None):
        headers = {
            "Content-type": "text/xml",
            "Accept": "application/xml"
        }
        # if not provided, fallback to name - this is what geoserver will do
        # anyway but nativeName needs to be provided if name is invalid xml
        # as this will cause verification errors since geoserver 2.6.1
        if nativeName is None:
            nativeName = name

        url = store.href.replace('.xml', '/wmslayers')
        data = "<wmsLayer><name>{}</name><nativeName>{}</nativeName></wmsLayer>".format(name, nativeName)
        resp = self.http_request(url, method='post', data=data, headers=headers)

        if resp.status_code not in (200, 201):
            raise FailedRequestError('Failed to create WMS layer: {}, {}'.format(resp.status_code, resp.text))

        self._cache.clear()
        return self.get_layer(name)

    def add_data_to_store(self, store, name, data, workspace=None, overwrite = False, charset = None):
        if isinstance(store, basestring):
            store = self.get_stores(names=store, workspaces=workspace)[0]
        if workspace is not None:
            workspace = _name(workspace)
            assert store.workspace.name == workspace, "Specified store (%s) is not in specified workspace (%s)!" % (store, workspace)
        else:
            workspace = store.workspace.name
        store = store.name

        if isinstance(data, dict):
            bundle = prepare_upload_bundle(name, data)
        else:
            bundle = data

        params = dict()
        if overwrite:
            params["update"] = "overwrite"
        if charset is not None:
            params["charset"] = charset

        headers = {'Content-Type': 'application/zip', 'Accept': 'application/xml'}
        upload_url = build_url(
            self.service_url,
            [
                "workspaces",
                workspace,
                "datastores",
                store,
                "file.shp"
            ],
            params
        )

        try:
            with open(bundle, "rb") as f:
                data = f.read()
                resp = self.http_request(upload_url, method='put', data=data, headers=headers)
                if resp.status_code != 201:
                    FailedRequestError('Failed to add data to store {} : {}, {}'.format(store, resp.status_code, resp.text))
                self._cache.clear()
        finally:
            os.unlink(bundle)

    def create_featurestore(self, name, data, workspace=None, overwrite=False, charset=None):
        if workspace is None:
            workspace = self.get_default_workspace()
        workspace = _name(workspace)

        if not overwrite:
            stores = self.get_stores(names=name, workspaces=workspace)
            if len(stores) > 0:
                msg = "There is already a store named {} in workspace {}".format(name, workspace)
                raise ConflictingDataError(msg)

        params = dict()
        if charset is not None:
            params['charset'] = charset
        url = build_url(
            self.service_url,
            [
                "workspaces",
                workspace,
                "datastores",
                name,
                "file.shp"
            ],
            params
        )

        # PUT /workspaces/<ws>/datastores/<ds>/file.shp
        headers = {
            "Content-type": "application/zip",
            "Accept": "application/xml"
        }
        if isinstance(data, dict):
            logger.debug('Data is NOT a zipfile')
            archive = prepare_upload_bundle(name, data)
        else:
            logger.debug('Data is a zipfile')
            archive = data
        file_obj = open(archive, 'rb')
        try:
            resp = self.http_request(url, method='put', data=file_obj, headers=headers)
            if resp.status_code != 201:
                FailedRequestError('Failed to create FeatureStore {} : {}, {}'.format(name, resp.status_code, resp.text))
            self._cache.clear()
        finally:
            file_obj.close()
            os.unlink(archive)

    def create_imagemosaic(self, name, data, configure='first', workspace=None, overwrite=False, charset=None):
        if workspace is None:
            workspace = self.get_default_workspace()
        workspace = _name(workspace)

        if not overwrite:
            store = self.get_stores(names=name, workspaces=workspace)
            if store:
                raise ConflictingDataError("There is already a store named {}".format(name))

        params = dict()
        if charset is not None:
            params['charset'] = charset
        if configure.lower() not in ('first', 'none', 'all'):
            raise ValueError("configure most be one of: first, none, all")
        params['configure'] = configure.lower()

        store_type = "file.imagemosaic"
        contet_type = "application/zip"

        if hasattr(data, 'read'):
            # Adding this check only to pass tests. We should drop support for passing a file object
            upload_data = data
        elif isinstance(data, basestring):
            if os.path.splitext(data)[-1] == ".zip":
                upload_data = open(data, 'rb')
            else:
                store_type = "external.imagemosaic"
                contet_type = "text/plain"
                upload_data = data if data.startswith("file:") else "file:{data}".format(data=data)
        else:
            raise ValueError("ImageMosaic Dataset or directory: {data} is incorrect".format(data=data))

        url = build_url(
            self.service_url,
            [
                "workspaces",
                workspace,
                "coveragestores",
                name,
                store_type
            ],
            params
        )

        # PUT /workspaces/<ws>/coveragestores/<name>/file.imagemosaic?configure=none
        headers = {
            "Content-type": contet_type,
            "Accept": "application/xml"
        }

        try:
            resp = self.http_request(url, method='put', data=upload_data, headers=headers)
            if resp.status_code != 201:
                FailedRequestError('Failed to create ImageMosaic {} : {}, {}'.format(name, resp.status_code, resp.text))
            self._cache.clear()
        finally:
            if hasattr(upload_data, "close"):
                upload_data.close()

        return self.get_stores(names=name, workspaces=workspace)[0]

    def create_coveragestore(self, name, workspace=None, path=None, type='GeoTIFF', create_layer=True, layer_name=None, source_name=None):
        """
        Create a coveragestore for locally hosted rasters.
        If create_layer is set to true, will create a coverage/layer.
        layer_name and source_name are only used if create_layer ia enabled. If not specified, the raster name will be used for both.
        """
        if path is None:
            raise Exception('You must provide a full path to the raster')

        allowed_types = [
            'ImageMosaic',
            'GeoTIFF',
            'Gtopo30',
            'WorldImage',
            'AIG',
            'ArcGrid',
            'DTED',
            'EHdr',
            'ERDASImg',
            'ENVIHdr',
            'GeoPackage (mosaic)',
            'NITF',
            'RPFTOC',
            'RST',
            'VRT'
        ]

        if type is None:
            raise Exception('Type must be declared')
        elif type not in allowed_types:
            raise Exception('Type must be one of {}'.format(", ".join(allowed_types)))

        if workspace is None:
            workspace = self.get_default_workspace()
        workspace = _name(workspace)

        cs = UnsavedCoverageStore(self, name, workspace)
        cs.type = type
        cs.url = path if path.startswith("file:") else "file:{}".format(path)
        self.save(cs)

        if create_layer:
            if layer_name is None:
                layer_name = os.path.splitext(os.path.basename(path))[0]
            if source_name is None:
                source_name = os.path.splitext(os.path.basename(path))[0]

            data = "<coverage><name>{}</name><nativeName>{}</nativeName></coverage>".format(layer_name, source_name)
            url = "{}/workspaces/{}/coveragestores/{}/coverages.xml".format(self.service_url, workspace, name)
            headers = {"Content-type": "application/xml"}

            resp = self.http_request(url, method='post', data=data, headers=headers)
            if resp.status_code != 201:
                FailedRequestError('Failed to create coverage/layer {} for : {}, {}'.format(layer_name, name, resp.status_code, resp.text))
            self._cache.clear()
            return self.get_resources(names=layer_name, workspaces=workspace)[0]
        return self.get_stores(names=name, workspaces=workspace)[0]

    def add_granule(self, data, store, workspace=None):
        '''Harvest/add a granule into an existing imagemosaic'''
        ext = os.path.splitext(data)[-1]
        if ext == ".zip":
            type = "file.imagemosaic"
            upload_data = open(data, 'rb')
            headers = {
                "Content-type": "application/zip",
                "Accept": "application/xml"
            }
        else:
            type = "external.imagemosaic"
            upload_data = data if data.startswith("file:") else "file:{data}".format(data=data)
            headers = {
                "Content-type": "text/plain",
                "Accept": "application/xml"
            }

        params = dict()
        workspace_name = workspace
        if isinstance(store, basestring):
            store_name = store
        else:
            store_name = store.name
            workspace_name = store.workspace.name

        if workspace_name is None:
            raise ValueError("Must specify workspace")

        url = build_url(
            self.service_url,
            [
                "workspaces",
                workspace_name,
                "coveragestores",
                store_name,
                type
            ],
            params
        )

        try:
            resp = self.http_request(url, method='post', data=upload_data, headers=headers)
            if resp.status_code != 202:
                FailedRequestError('Failed to add granule to mosaic {} : {}, {}'.format(store, resp.status_code, resp.text))
            self._cache.clear()
        finally:
            if hasattr(upload_data, "close"):
                upload_data.close()

        # maybe return a list of all granules?
        return None

    def delete_granule(self, coverage, store, granule_id, workspace=None):
        '''Deletes a granule of an existing imagemosaic'''
        params = dict()

        workspace_name = workspace
        if isinstance(store, basestring):
            store_name = store
        else:
            store_name = store.name
            workspace_name = store.workspace.name

        if workspace_name is None:
            raise ValueError("Must specify workspace")

        url = build_url(
            self.service_url,
            [
                "workspaces",
                workspace_name,
                "coveragestores",
                store_name,
                "coverages",
                coverage,
                "index/granules",
                granule_id,
                ".json"
            ],
            params
        )

        # DELETE /workspaces/<ws>/coveragestores/<name>/coverages/<coverage>/index/granules/<granule_id>.json
        headers = {
            "Content-type": "application/json",
            "Accept": "application/json"
        }

        resp = self.http_request(url, method='delete', headers=headers)
        if resp.status_code != 200:
            FailedRequestError('Failed to delete granule from mosaic {} : {}, {}'.format(store, resp.status_code, resp.text))
        self._cache.clear()

        # maybe return a list of all granules?
        return None

    def list_granules(self, coverage, store, workspace=None, filter=None, limit=None, offset=None):
        '''List granules of an imagemosaic'''
        params = dict()

        if filter is not None:
            params['filter'] = filter
        if limit is not None:
            params['limit'] = limit
        if offset is not None:
            params['offset'] = offset

        workspace_name = workspace
        if isinstance(store, basestring):
            store_name = store
        else:
            store_name = store.name
            workspace_name = store.workspace.name

        if workspace_name is None:
            raise ValueError("Must specify workspace")

        url = build_url(
            self.service_url,
            [
                "workspaces",
                workspace_name,
                "coveragestores",
                store_name,
                "coverages",
                coverage,
                "index/granules.json"
            ],
            params
        )

        # GET /workspaces/<ws>/coveragestores/<name>/coverages/<coverage>/index/granules.json
        headers = {
            "Content-type": "application/json",
            "Accept": "application/json"
        }

        resp = self.http_request(url, headers=headers)
        if resp.status_code != 200:
            FailedRequestError('Failed to list granules in mosaic {} : {}, {}'.format(store, resp.status_code, resp.text))

        self._cache.clear()
        return resp.json()

    def mosaic_coverages(self, store):
        '''Returns all coverages in a coverage store'''
        params = dict()
        url = build_url(
            self.service_url,
            [
                "workspaces",
                store.workspace.name,
                "coveragestores",
                store.name,
                "coverages.json"
            ],
            params
        )
        # GET /workspaces/<ws>/coveragestores/<name>/coverages.json
        headers = {
            "Content-type": "application/json",
            "Accept": "application/json"
        }

        resp = self.http_request(url, headers=headers)
        if resp.status_code != 200:
            FailedRequestError('Failed to get mosaic coverages {} : {}, {}'.format(store, resp.status_code, resp.text))

        self._cache.clear()
        return resp.json()

    def mosaic_coverage_schema(self, coverage, store, workspace):
        '''Returns the schema of a coverage in a coverage store'''
        params = dict()
        url = build_url(
            self.service_url,
            [
                "workspaces",
                workspace,
                "coveragestores",
                store,
                "coverages",
                coverage,
                "index.json"
            ],
            params
        )
        # GET /workspaces/<ws>/coveragestores/<name>/coverages/<coverage>/index.json

        headers = {
            "Content-type": "application/json",
            "Accept": "application/json"
        }

        resp = self.http_request(url, headers=headers)
        if resp.status_code != 200:
            FailedRequestError('Failed to get mosaic schema {} : {}, {}'.format(store, resp.status_code, resp.text))

        self._cache.clear()
        return resp.json()

    def publish_featuretype(self, name, store, native_crs, srs=None, jdbc_virtual_table=None, native_name=None):
        '''Publish a featuretype from data in an existing store'''
        # @todo native_srs doesn't seem to get detected, even when in the DB
        # metadata (at least for postgis in geometry_columns) and then there
        # will be a misconfigured layer
        if native_crs is None:
            raise ValueError("must specify native_crs")

        if jdbc_virtual_table is None and native_name is None:
            raise ValueError("must specify native_name")

        srs = srs or native_crs
        feature_type = FeatureType(self, store.workspace, store, name)
        # because name is the in FeatureType base class, work around that
        # and hack in these others that don't have xml properties
        feature_type.dirty['name'] = name
        feature_type.dirty['srs'] = srs
        feature_type.dirty['nativeCRS'] = native_crs
        feature_type.enabled = True
        feature_type.advertised = True
        feature_type.title = name

        if native_name is not None:
            feature_type.native_name = native_name

        headers = {
            "Content-type": "application/xml",
            "Accept": "application/xml"
        }

        resource_url = store.resource_url
        if jdbc_virtual_table is not None:
            feature_type.metadata = ({'JDBC_VIRTUAL_TABLE': jdbc_virtual_table})
            params = dict()
            resource_url = build_url(
                self.service_url,
                [
                    "workspaces",
                    store.workspace.name,
                    "datastores", store.name,
                    "featuretypes.xml"
                ],
                params
            )

        resp = self.http_request(resource_url, method='post', data=feature_type.message(), headers=headers)
        if resp.status_code not in (200, 201, 202):
            FailedRequestError('Failed to publish feature type {} : {}, {}'.format(name, resp.status_code, resp.text))

        self._cache.clear()
        feature_type.fetch()
        return feature_type

    def get_resources(self, names=None, stores=None, workspaces=None):
        '''
        Resources include feature stores, coverage stores and WMS stores, however does not include layer groups.
        names, stores and workspaces can be provided as a comma delimited strings or as arrays, and are used for filtering.
        Will always return an array.
        '''

        stores = self.get_stores(
            names = stores,
            workspaces = workspaces
        )

        resources = []
        for s in stores:
            try:
                resources.extend(s.get_resources())
            except FailedRequestError:
                continue

        if names is None:
            names = []
        elif isinstance(names, basestring):
            names = [s.strip() for s in names.split(',') if s.strip()]

        if resources and names:
            return ([resource for resource in resources if resource.name in names])

        return resources

    def get_layer(self, name):
        try:
            lyr = Layer(self, name)
            lyr.fetch()
            return lyr
        except FailedRequestError:
            return None

    def get_layers(self, resource=None):
        if isinstance(resource, basestring):
            resource = self.get_resources(names = resource)[0]
        layers_url = "{}/layers.xml".format(self.service_url)
        data = self.get_xml(layers_url)
        lyrs = [Layer(self, l.find("name").text) for l in data.findall("layer")]
        if resource is not None:
            lyrs = [l for l in lyrs if l.resource.href == resource.href]
        # TODO: Filter by style
        return lyrs

    def get_layergroups(self, names=None, workspaces=None):
        '''
        names and workspaces can be provided as a comma delimited strings or as arrays, and are used for filtering.
        If no workspaces are provided, will return all layer groups in the catalog (global and workspace specific).
        Will always return an array.
        '''

        layergroups = []

        if workspaces is None or len(workspaces) == 0:
            # Add global layergroups
            url = "{}/layergroups.xml".format(self.service_url)
            groups = self.get_xml(url)
            layergroups.extend([LayerGroup(self, g.find("name").text, None) for g in groups.findall("layerGroup")])
            workspaces = []
        elif isinstance(workspaces, basestring):
            workspaces = [s.strip() for s in workspaces.split(',') if s.strip()]
        elif isinstance(workspaces, Workspace):
            workspaces = [workspaces]

        if not workspaces:
            workspaces = self.get_workspaces()

        for ws in workspaces:
            ws_name = _name(ws)
            url = "{}/workspaces/{}/layergroups.xml".format(self.service_url, ws_name)
            try:
                groups = self.get_xml(url)
            except FailedRequestError as e:
                if "no such workspace" in str(e).lower():
                    continue
                else:
                    raise FailedRequestError("Failed to get layergroups: {}".format(e))

            layergroups.extend([LayerGroup(self, g.find("name").text, ws_name) for g in groups.findall("layerGroup")])

        if names is None:
            names = []
        elif isinstance(names, basestring):
            names = [s.strip() for s in names.split(',') if s.strip()]

        if layergroups and names:
            return ([lg for lg in layergroups if lg.name in names])

        return layergroups

    def create_layergroup(self, name, layers = (), styles = (), bounds = None, mode = "SINGLE", abstract = None,
                          title = None, workspace = None):
        if self.get_layergroups(names=name, workspaces=workspace):
            raise ConflictingDataError("LayerGroup named %s already exists!" % name)
        else:
            return UnsavedLayerGroup(self, name, layers, styles, bounds, mode, abstract, title, workspace)

    def get_styles(self, names=None, workspaces=None):
        '''
        names and workspaces can be provided as a comma delimited strings or as arrays, and are used for filtering.
        If no workspaces are provided, will return all styles in the catalog (global and workspace specific).
        Will always return an array.
        '''

        all_styles = []

        if workspaces is None:
            # Add global styles
            url = "{}/styles.xml".format(self.service_url)
            styles = self.get_xml(url)
            all_styles.extend([Style(self, s.find('name').text) for s in styles.findall("style")])
            workspaces = []
        elif isinstance(workspaces, basestring):
            workspaces = [s.strip() for s in workspaces.split(',') if s.strip()]
        elif isinstance(workspaces, Workspace):
            workspaces = [workspaces]

        if not workspaces:
            workspaces = self.get_workspaces()

        for ws in workspaces:
            url = "{}/workspaces/{}/styles.xml".format(self.service_url, _name(ws))
            try:
                styles = self.get_xml(url)
            except FailedRequestError as e:
                if "no such workspace" in str(e).lower():
                    continue
                elif "workspace {} not found".format(_name(ws)) in str(e).lower():
                    continue
                else:
                    raise FailedRequestError("Failed to get styles: {}".format(e))

            all_styles.extend([Style(self, s.find("name").text, _name(ws)) for s in styles.findall("style")])

        if names is None:
            names = []
        elif isinstance(names, basestring):
            names = [s.strip() for s in names.split(',') if s.strip()]

        if all_styles and names:
            return ([style for style in all_styles if style.name in names])

        return all_styles

    def create_style(self, name, data, overwrite = False, workspace=None, style_format="sld10", raw=False):
        styles = self.get_styles(names=name, workspaces=workspace)
        if len(styles) > 0:
            style = styles[0]
        else:
            style = None

        if not overwrite and style is not None:
            raise ConflictingDataError("There is already a style named %s" % name)

        if style is None:
            headers = {
                "Content-type": "application/xml",
                "Accept": "application/xml"
            }
            xml = "<style><name>{0}</name><filename>{0}.sld</filename></style>".format(name)
            style = Style(self, name, workspace, style_format)

            resp = self.http_request(style.create_href, method='post', data=xml, headers=headers)
            if resp.status_code not in (200, 201, 202):
                FailedRequestError('Failed to create style {} : {}, {}'.format(name, resp.status_code, resp.text))

        headers = {
            "Content-type": style.content_type,
            "Accept": "application/xml"
        }

        body_href = style.body_href
        if raw:
            body_href += "?raw=true"

        resp = self.http_request(body_href, method='put', data=data, headers=headers)
        if resp.status_code not in (200, 201, 202):
            FailedRequestError('Failed to create style {} : {}, {}'.format(name, resp.status_code, resp.text))

        self._cache.pop(style.href, None)
        self._cache.pop(style.body_href, None)

    def create_workspace(self, name, uri):
        xml = (
            "<namespace>"
            "<prefix>{name}</prefix>"
            "<uri>{uri}</uri>"
            "</namespace>"
        ).format(name=name, uri=uri)

        headers = {"Content-Type": "application/xml"}
        workspace_url = self.service_url + "/namespaces/"

        resp = self.http_request(workspace_url, method='post', data=xml, headers=headers)
        if resp.status_code not in (200, 201, 202):
            FailedRequestError('Failed to create workspace {} : {}, {}'.format(name, resp.status_code, resp.text))

        self._cache.pop("{}/workspaces.xml".format(self.service_url), None)
        workspaces = self.get_workspaces(names=name)
        # Can only have one workspace with this name
        return workspaces[0] if workspaces else None

    def get_workspaces(self, names=None):
        '''
          Returns a list of workspaces in the catalog.
          If names is specified, will only return workspaces that match.
          names can either be a comma delimited string or an array.
          Will return an empty list if no workspaces are found.
        '''
        if names is None:
            names = []
        elif isinstance(names, basestring):
            names = [s.strip() for s in names.split(',') if s.strip()]

        data = self.get_xml("{}/workspaces.xml".format(self.service_url))
        workspaces = []
        workspaces.extend([workspace_from_index(self, node) for node in data.findall("workspace")])

        if workspaces and names:
            return ([ws for ws in workspaces if ws.name in names])

        return workspaces

    def get_default_workspace(self):
        ws = Workspace(self, "default")
        # must fetch and resolve the 'real' workspace from the response
        ws.fetch()
        return workspace_from_index(self, ws.dom)

    def set_default_workspace(self, name):
        if hasattr(name, 'name'):
            name = name.name
        workspace = self.get_workspaces(names=name)[0]
        if workspace is not None:
            headers = {"Content-Type": "application/xml"}
            default_workspace_url = self.service_url + "/workspaces/default.xml"
            data = "<workspace><name>{}</name></workspace>".format(name)

            resp = self.http_request(default_workspace_url, method='put', data=data, headers=headers)
            if resp.status_code not in (200, 201, 202):
                FailedRequestError('Failed to set default workspace {} : {}, {}'.format(name, resp.status_code, resp.text))

            self._cache.pop(default_workspace_url, None)
            self._cache.pop("{}/workspaces.xml".format(self.service_url), None)
        else:
            raise FailedRequestError("no workspace named {}".format(name))

    def list_feature_type_names(self, workspace, store, filter='available'):
        if workspace is None:
            raise ValueError("Must provide workspace")

        if store is None:
            raise ValueError("Must provide store")

        filter = filter.lower()
        workspace = _name(workspace)
        store = _name(store)

        url = "{}/workspaces/{}/datastores/{}/featuretypes.json?list={}".format(self.service_url, workspace, store, filter)
        resp = self.http_request(url)
        if resp.status_code != 200:
            FailedRequestError('Failed to query feature_type_names')

        data = []
        if filter in ('available', 'available_with_geom'):
            try:
                data = resp.json()['list']['string']
            except JSONDecodeError:
                pass
            return data
        elif filter == 'configured':
            data = resp.json()['featureTypes']['featureType']
            return [fn['name'] for fn in data]
        elif filter == 'all':
            feature_type_names = []
            url = "{}/workspaces/{}/datastores/{}/featuretypes.json?list=available".format(self.service_url, workspace, store)
            resp = self.http_request(url)
            if resp.status_code != 200:
                FailedRequestError('Failed to query feature_type_names')
            feature_type_names.extend(resp.json()['list']['string'])

            url = "{}/workspaces/{}/datastores/{}/featuretypes.json?list=configured".format(self.service_url, workspace, store)
            resp = self.http_request(url)
            if resp.status_code != 200:
                FailedRequestError('Failed to query feature_type_names')
            data = resp.json()['featureTypes']['featureType']
            feature_type_names.extend([fn['name'] for fn in data])

            return feature_type_names
