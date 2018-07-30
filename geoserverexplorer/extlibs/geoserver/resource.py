'''
gsconfig is a python library for manipulating a GeoServer instance via the GeoServer RESTConfig API.

The project is distributed under a MIT License .
'''

from geoserver.support import (ResourceInfo, xml_property, write_string, bbox, metadata, write_metadata,
                               write_bbox, string_list, write_string_list, attribute_list, write_bool, build_url)

try:
    from past.builtins import basestring
except ImportError:
    pass


def md_link(node):
    """Extract a metadata link tuple from an xml node"""
    mimetype = node.find("type")
    mdtype = node.find("metadataType")
    content = node.find("content")
    if None in [mimetype, mdtype, content]:
        return None
    else:
        return (mimetype.text, mdtype.text, content.text)


def metadata_link_list(node):
    if node is not None:
        return [md_link(n) for n in node.findall("metadataLink")]


def write_metadata_link_list(name):
    def write(builder, md_links):
        builder.start(name, dict())
        if md_links:
            for (mime, md_type, content_url) in md_links:
                # geoserver supports only three mime
                if md_type not in ['ISO19115:2003', 'FGDC', 'TC211']:
                    mime = 'other'
                    md_type = 'other'
                builder.start("metadataLink", dict())
                builder.start("type", dict())
                builder.data(mime)
                builder.end("type")
                builder.start("metadataType", dict())
                builder.data(md_type)
                builder.end("metadataType")
                builder.start("content", dict())
                builder.data(content_url)
                builder.end("content")
                builder.end("metadataLink")
        builder.end(name)
    return write


def featuretype_from_index(catalog, workspace, store, node):
    name = node.find("name")
    return FeatureType(catalog, workspace, store, name.text)


def coverage_from_index(catalog, workspace, store, node):
    name = node.find("name")
    return Coverage(catalog, workspace, store, name.text)


def wmslayer_from_index(catalog, workspace, store, node):
    name = node.find("name")
    return WmsLayer(catalog, workspace, store, name.text)


class _ResourceBase(ResourceInfo):
    save_method = 'PUT'

    def __init__(self, catalog, workspace, store, name, href=None):
        super(_ResourceBase, self).__init__()

        if not href:
            assert isinstance(store, ResourceInfo)
            assert isinstance(name, basestring)
            assert workspace is not None
        else:
            parts = href.split('/')
            self._workspace_name = parts[parts.index('workspaces') + 1]
            self._store_name = parts[parts.index(self.url_part_stores) + 1]
            name = parts[-1].replace('.xml', '')

        self._href = href
        self.catalog = catalog
        self._workspace = workspace
        self._store = store
        self.name = name

    @property
    def workspace(self):
        if not self._workspace:
            self._workspace = self.catalog.get_workspaces(self._workspace_name)[0]
        return self._workspace

    @property
    def store(self):
        if not self._store:
            self._store = self.catalog.get_stores(names=self._store_name, workspaces=self._workspace_name)
        return self._store

    @property
    def href(self):
        url = build_url(
            self.catalog.service_url,
            [
                "workspaces",
                self.workspace.name,
                self.url_part_stores,
                self.store.name,
                self.url_part_types,
                self.name + ".xml"
            ]
        )
        return self._href or url


class FeatureType(_ResourceBase):

    resource_type = "featureType"
    url_part_stores = 'datastores'
    url_part_types = 'featuretypes'

    title = xml_property("title")
    native_name = xml_property("nativeName")
    abstract = xml_property("abstract")
    enabled = xml_property("enabled")
    advertised = xml_property("advertised", default="true")
    native_bbox = xml_property("nativeBoundingBox", bbox)
    latlon_bbox = xml_property("latLonBoundingBox", bbox)
    projection = xml_property("srs")
    projection_policy = xml_property("projectionPolicy")
    keywords = xml_property("keywords", string_list)
    attributes = xml_property("attributes", attribute_list)
    metadata_links = xml_property("metadataLinks", metadata_link_list)
    metadata = xml_property("metadata", metadata)

    writers = dict(
        name = write_string("name"),
        nativeName = write_string("nativeName"),
        title = write_string("title"),
        abstract = write_string("abstract"),
        enabled = write_bool("enabled"),
        advertised = write_bool("advertised"),
        nativeBoundingBox = write_bbox("nativeBoundingBox"),
        latLonBoundingBox = write_bbox("latLonBoundingBox"),
        srs = write_string("srs"),
        nativeCRS = write_string("nativeCRS"),
        projectionPolicy = write_string("projectionPolicy"),
        keywords = write_string_list("keywords"),
        metadataLinks = write_metadata_link_list("metadataLinks"),
        metadata = write_metadata("metadata")
    )


class CoverageDimension(object):
    def __init__(self, name, description, dimension_range):
        self.name = name
        self.description = description
        self.dimension_range = dimension_range


def coverage_dimension(node):
    name = node.find("name")
    name = name.text if name is not None else None
    description = node.find("description")
    description = description.text if description is not None else None
    range_min = node.find("range/min")
    range_max = node.find("range/max")
    dimension_range = None
    if None not in [min, max]:
        dimension_range = float(range_min.text), float(range_max.text)
    if None not in [name, description]:
        return CoverageDimension(name, description, dimension_range)
    else:
        # should we bomb out more spectacularly here?
        return None


def coverage_dimension_xml(builder, dimension):
    builder.start("coverageDimension", dict())
    builder.start("name", dict())
    builder.data(dimension.name)
    builder.end("name")

    builder.start("description", dict())
    builder.data(dimension.description)
    builder.end("description")

    if dimension.range is not None:
        builder.start("range", dict())
        builder.start("min", dict())
        builder.data(str(dimension.range[0]))
        builder.end("min")
        builder.start("max", dict())
        builder.data(str(dimension.range[1]))
        builder.end("max")
        builder.end("range")

    builder.end("coverageDimension")


class Coverage(_ResourceBase):

    resource_type = "coverage"
    url_part_stores = 'coveragestores'
    url_part_types = 'coverages'

    title = xml_property("title")
    native_name = xml_property("nativeName")
    native_format = xml_property("nativeFormat")
    native_crs = xml_property("nativeCRS")
    default_interpolation_method = xml_property("defaultInterpolationMethod")
    abstract = xml_property("abstract")
    description = xml_property("description")
    enabled = xml_property("enabled")
    advertised = xml_property("advertised", default="true")
    native_bbox = xml_property("nativeBoundingBox", bbox)
    latlon_bbox = xml_property("latLonBoundingBox", bbox)
    projection = xml_property("srs")
    projection_policy = xml_property("projectionPolicy")
    keywords = xml_property("keywords", string_list)
    request_srs_list = xml_property("requestSRS", string_list)
    response_srs_list = xml_property("responseSRS", string_list)
    supported_formats = xml_property("supportedFormats", string_list)
    metadata_links = xml_property("metadataLinks", metadata_link_list)
    metadata = xml_property("metadata", metadata)
    interpolation_methods = xml_property("interpolationMethods", string_list)

    writers = dict(
        title = write_string("title"),
        native_name = write_string("nativeName"),
        native_format = write_string("nativeFormat"),
        native_crs = write_string("nativeCRS"),
        default_interpolation_method = write_string("defaultInterpolationMethod"),
        description = write_string("description"),
        abstract = write_string("abstract"),
        enabled = write_bool("enabled"),
        advertised = write_bool("advertised"),
        nativeBoundingBox = write_bbox("nativeBoundingBox"),
        latLonBoundingBox = write_bbox("latLonBoundingBox"),
        srs = write_string("srs"),
        projection_policy = write_string("projectionPolicy"),
        keywords = write_string_list("keywords"),
        metadataLinks = write_metadata_link_list("metadataLinks"),
        requestSRS = write_string_list("requestSRS"),
        responseSRS = write_string_list("responseSRS"),
        supportedFormats = write_string_list("supportedFormats"),
        interpolation_methods = write_string_list("interpolationMethods"),
        metadata = write_metadata("metadata")
    )


class WmsLayer(ResourceInfo):

    resource_type = "wmsLayer"
    save_method = "PUT"

    def __init__(self, catalog, workspace, store, name):
        super(WmsLayer, self).__init__()
        self.catalog = catalog
        self.workspace = workspace
        self.store = store
        self.name = name

    @property
    def href(self):
        url = "{}/workspaces/{}/wmsstores/{}/wmslayers/{}.xml".format(
            self.catalog.service_url,
            self.workspace.name,
            self.store.name,
            self.name
        )
        return url

    title = xml_property("title")
    description = xml_property("description")
    abstract = xml_property("abstract")
    keywords = xml_property("keywords", string_list)
    projection = xml_property("srs")
    native_bbox = xml_property("nativeBoundingBox", bbox)
    latlon_bbox = xml_property("latLonBoundingBox", bbox)
    projection_policy = xml_property("projectionPolicy")
    enabled = xml_property("enabled", lambda x: x.text == "true")
    advertised = xml_property("advertised", lambda x: x.text == "true", default=True)
    metadata_links = xml_property("metadataLinks", metadata_link_list)

    writers = dict(
        title = write_string("title"),
        description = write_string("description"),
        abstract = write_string("abstract"),
        keywords = write_string_list("keywords"),
        # nativeCRS
        srs = write_string("srs"),
        nativeBoundingBox = write_bbox("nativeBoundingBox"),
        latLonBoundingBox = write_bbox("latLonBoundingBox"),
        projectionPolicy = write_string("projectionPolicy"),
        enabled = write_bool("enabled"),
        advertised = write_bool("advertised"),
        metadataLinks = write_metadata_link_list("metadataLinks")
    )
