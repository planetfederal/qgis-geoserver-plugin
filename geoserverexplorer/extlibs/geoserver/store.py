'''
gsconfig is a python library for manipulating a GeoServer instance via the GeoServer RESTConfig API.

The project is distributed under a MIT License .
'''

import geoserver.workspace as ws
from geoserver.resource import featuretype_from_index, coverage_from_index, wmslayer_from_index
from geoserver.support import ResourceInfo, xml_property, key_value_pairs, write_bool, write_dict, write_string, build_url

try:
    from past.builtins import basestring
except ImportError:
    pass


def datastore_from_index(catalog, workspace, node):
    name = node.find("name")
    return DataStore(catalog, workspace, name.text)


def coveragestore_from_index(catalog, workspace, node):
    name = node.find("name")
    return CoverageStore(catalog, workspace, name.text)


def wmsstore_from_index(catalog, workspace, node):
    name = node.find("name")
    # user = node.find("user")
    # password = node.find("password")
    return WmsStore(catalog, workspace, name.text, None, None)


class DataStore(ResourceInfo):

    resource_type = "dataStore"
    save_method = "PUT"

    def __init__(self, catalog, workspace, name):
        super(DataStore, self).__init__()

        assert isinstance(workspace, ws.Workspace)
        assert isinstance(name, basestring)
        self.catalog = catalog
        self.workspace = workspace
        self.name = name

    @property
    def href(self):
        url = build_url(
            self.catalog.service_url,
            [
                "workspaces",
                self.workspace.name,
                "datastores",
                self.name + ".xml"
            ]
        )
        return url

    enabled = xml_property("enabled", lambda x: x.text == "true")
    name = xml_property("name")
    type = xml_property("type")
    connection_parameters = xml_property("connectionParameters", key_value_pairs)

    writers = dict(
        enabled = write_bool("enabled"),
        name = write_string("name"),
        type = write_string("type"),
        connectionParameters = write_dict("connectionParameters")
    )

    @property
    def resource_url(self):
        url = build_url(
            self.catalog.service_url,
            [
                "workspaces",
                self.workspace.name,
                "datastores",
                self.name,
                "featuretypes.xml"
            ]
        )
        return url

    def get_resources(self, name=None, available=False):
        res_url = self.resource_url
        if available:
            res_url += "?list=available"
        xml = self.catalog.get_xml(res_url)

        def ft_from_node(node):
            return featuretype_from_index(self.catalog, self.workspace, self, node)

        # if name passed, return only one FeatureType, otherwise return all FeatureTypes in store:
        if name is not None:
            for node in xml.findall("featureType"):
                if node.findtext("name") == name:
                    return ft_from_node(node)
            return None
        if available:
            return [str(node.text) for node in xml.findall("featureTypeName")]
        else:
            return [ft_from_node(node) for node in xml.findall("featureType")]


class UnsavedDataStore(DataStore):

    save_method = "POST"

    def __init__(self, catalog, name, workspace):
        super(UnsavedDataStore, self).__init__(catalog, workspace, name)
        self.dirty.update(dict(
            name=name, enabled=True, type=None,
            connectionParameters=dict()))

    @property
    def href(self):
        path = [
            "workspaces",
            self.workspace.name,
            "datastores"
        ]
        query = dict(name=self.name)
        return build_url(self.catalog.service_url, path, query)


class CoverageStore(ResourceInfo):
    resource_type = 'coverageStore'
    save_method = "PUT"

    def __init__(self, catalog, workspace, name):
        super(CoverageStore, self).__init__()

        self.catalog = catalog
        self.workspace = workspace
        self.name = name

    @property
    def href(self):
        url = build_url(
            self.catalog.service_url,
            [
                "workspaces",
                self.workspace.name,
                "coveragestores",
                "{}.xml".format(self.name)
            ]
        )
        return url

    enabled = xml_property("enabled", lambda x: x.text == "true")
    name = xml_property("name")
    url = xml_property("url")
    type = xml_property("type")

    writers = dict(
        enabled = write_bool("enabled"),
        name = write_string("name"),
        url = write_string("url"),
        type = write_string("type"),
        workspace = write_string("workspace")
    )

    def get_resources(self, name=None):
        res_url = build_url(
            self.catalog.service_url,
            [
                "workspaces",
                self.workspace.name,
                "coveragestores",
                self.name,
                "coverages.xml"
            ]
        )

        xml = self.catalog.get_xml(res_url)

        def cov_from_node(node):
            return coverage_from_index(self.catalog, self.workspace, self, node)

        # if name passed, return only one Coverage, otherwise return all Coverages in store:
        if name is not None:
            for node in xml.findall("coverage"):
                if node.findtext("name") == name:
                    return cov_from_node(node)
            return None
        return [cov_from_node(node) for node in xml.findall("coverage")]


class UnsavedCoverageStore(CoverageStore):
    save_method = "POST"

    def __init__(self, catalog, name, workspace):
        super(UnsavedCoverageStore, self).__init__(catalog, workspace, name)
        self.dirty.update(
            name = name,
            enabled = True,
            type = 'GeoTIFF',
            url = "file:data/",
            workspace = workspace
        )

    @property
    def href(self):
        url = build_url(
            self.catalog.service_url,
            [
                "workspaces",
                self.workspace,
                "coveragestores"
            ],
            dict(name=self.name)
        )
        return url


class WmsStore(ResourceInfo):
    resource_type = "wmsStore"
    save_method = "PUT"

    def __init__(self, catalog, workspace, name, user, password):
        super(WmsStore, self).__init__()
        self.catalog = catalog
        self.workspace = workspace
        self.name = name
        self.metadata = {}
        self.metadata['user'] = user
        self.metadata['password'] = password

    @property
    def href(self):
        return "%s/workspaces/%s/wmsstores/%s.xml" % (self.catalog.service_url, self.workspace.name, self.name)

    enabled = xml_property("enabled", lambda x: x.text == "true")
    name = xml_property("name")
    nativeName = xml_property("nativeName")
    capabilitiesURL = xml_property("capabilitiesURL")
    type = xml_property("type")
    metadata = xml_property("metadata", key_value_pairs)

    writers = dict(enabled = write_bool("enabled"),
                   name = write_string("name"),
                   capabilitiesURL = write_string("capabilitiesURL"),
                   type = write_string("type"),
                   metadata = write_dict("metadata"))

    def get_resources(self, name=None, available=False):
        res_url = "{}/workspaces/{}/wmsstores/{}/wmslayers.xml".format(
            self.catalog.service_url,
            self.workspace.name,
            self.name
        )
        layer_name_attr = "wmsLayer"

        if available:
            res_url += "?list=available"
            layer_name_attr += 'Name'

        xml = self.catalog.get_xml(res_url)

        def wl_from_node(node):
            return wmslayer_from_index(self.catalog, self.workspace, self, node)

        # if name passed, return only one layer, otherwise return all layers in store:
        if name is not None:
            for node in xml.findall(layer_name_attr):
                if node.findtext("name") == name:
                    return wl_from_node(node)
            return None

        if available:
            return [str(node.text) for node in xml.findall(layer_name_attr)]
        else:
            return [wl_from_node(node) for node in xml.findall(layer_name_attr)]


class UnsavedWmsStore(WmsStore):
    save_method = "POST"

    def __init__(self, catalog, name, workspace, user, password):
        super(UnsavedWmsStore, self).__init__(catalog, workspace, name, user, password)
        metadata = {}
        if user is not None and password is not None:
            metadata['user'] = user
            metadata['password'] = password
        self.dirty.update(dict(
            name=name, enabled=True, capabilitiesURL="", type="WMS", metadata=metadata))

    @property
    def href(self):
        return "%s/workspaces/%s/wmsstores?name=%s" % (self.catalog.service_url, self.workspace.name, self.name)
