'''
gsconfig is a python library for manipulating a GeoServer instance via the GeoServer RESTConfig API.

The project is distributed under a MIT License .
'''

from geoserver.support import ResourceInfo, build_url, xml_property
try:
    from past.builtins import basestring
except ImportError:
    pass


class Style(ResourceInfo):
    supported_formats = ["sld10", "sld11", "zip"]
    content_types = {
        "sld10": "application/vnd.ogc.sld+xml",
        "sld11": "application/vnd.ogc.se+xml",
        "zip": "application/zip"
    }

    def __init__(self, catalog, name, workspace=None, style_format="sld10"):
        super(Style, self).__init__()
        assert isinstance(name, basestring)
        assert style_format in Style.supported_formats

        self.catalog = catalog
        self.workspace = workspace
        self.name = name
        self.style_format = style_format
        self._sld_dom = None

    @property
    def fqn(self):
        return self.name if not self.workspace else '%s:%s' % (self.workspace, self.name)

    @property
    def href(self):
        return self._build_href('.xml')

    @property
    def body_href(self):
        return self._build_href('.sld')

    @property
    def create_href(self):
        return self._build_href('.xml', True)

    @property
    def content_type(self):
        return Style.content_types[self.style_format]

    def _build_href(self, extension, create=False):
        path_parts = ["styles"]
        query = {}
        if not create:
            path_parts.append(self.name + extension)
        else:
            query['name'] = self.name
        if self.workspace is not None:
            path_parts = ["workspaces", getattr(self.workspace, 'name', self.workspace)] + path_parts
        return build_url(self.catalog.service_url, path_parts, query)

    filename = xml_property("filename")

    def _get_sld_dom(self):
        if self._sld_dom is None:
            self._sld_dom = self.catalog.get_xml(self.body_href)
        return self._sld_dom

    @property
    def sld_title(self):
        user_style = self._get_sld_dom().find("{http://www.opengis.net/sld}NamedLayer/{http://www.opengis.net/sld}UserStyle")
        if not user_style:
            user_style = self._get_sld_dom().find("{http://www.opengis.net/sld}UserLayer/{http://www.opengis.net/sld}UserStyle")

        if user_style:
            try:
                # it is not mandatory
                title_node = user_style.find("{http://www.opengis.net/sld}Title")
            except:
                title_node = None

        return title_node.text if title_node is not None else None

    @property
    def sld_name(self):
        user_style = self._get_sld_dom().find("{http://www.opengis.net/sld}NamedLayer/{http://www.opengis.net/sld}UserStyle")
        if not user_style:
            user_style = self._get_sld_dom().find("{http://www.opengis.net/sld}UserLayer/{http://www.opengis.net/sld}UserStyle")

        if user_style:
            try:
                # it is not mandatory
                name_node = user_style.find("{http://www.opengis.net/sld}Name")
            except:
                name_node = None

        return name_node.text if name_node is not None else None

    @property
    def sld_body(self):
        resp = self.catalog.http_request(self.body_href)
        return resp.content

    def update_body(self, body):
        headers = {"Content-Type": self.content_type}
        self.catalog.http_request(
            self.body_href, body, "PUT", headers)
