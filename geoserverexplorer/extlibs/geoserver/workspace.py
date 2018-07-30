'''
gsconfig is a python library for manipulating a GeoServer instance via the GeoServer RESTConfig API.

The project is distributed under a MIT License .
'''

from geoserver.support import xml_property, write_bool, ResourceInfo, build_url


def workspace_from_index(catalog, node):
    name = node.find("name")
    return Workspace(catalog, name.text)


class Workspace(ResourceInfo):

    resource_type = "workspace"

    def __init__(self, catalog, name):
        super(Workspace, self).__init__()
        self.catalog = catalog
        self.name = name

    @property
    def href(self):
        return build_url(self.catalog.service_url, ["workspaces", self.name + ".xml"])

    @property
    def coveragestore_url(self):
        return build_url(self.catalog.service_url, ["workspaces", self.name, "coveragestores.xml"])

    @property
    def datastore_url(self):
        return build_url(self.catalog.service_url, ["workspaces", self.name, "datastores.xml"])

    @property
    def wmsstore_url(self):
        return "%s/workspaces/%s/wmsstores.xml" % (self.catalog.service_url, self.name)

    def __repr__(self):
        return "%s @ %s" % (self.name, self.href)
