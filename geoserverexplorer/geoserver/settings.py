# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
import httplib2
from xml.etree.ElementTree import XML
import xml.etree.ElementTree as ET
from urlparse import urlparse
from geoserver.support import url
from geoserverexplorer.geoserver.pki import PKICatalog

class Settings(object):

    def __init__(self, catalog):
        self.catalog = catalog
        if isinstance(catalog, PKICatalog):
            http = httplib2.Http(ca_certs=catalog.ca_cert, disable_ssl_certificate_validation = False)
            http.add_certificate(catalog.key, catalog.cert, '')
        else:
            http = httplib2.Http()
            http.add_credentials(catalog.username, catalog.password)
            netloc = urlparse(self.catalog.service_url).netloc
            http.authorizations.append(
                httplib2.BasicAuthentication(
                    (catalog.username, catalog.password),
                    netloc,
                    self.catalog.service_url,
                    {},
                    None,
                    None,
                    http
                )
        )
        self.http = http

    def settings(self):
        settings = {}
        settings_url = url(self.catalog.service_url, ['settings.xml'])
        headers, response = self.http.request(settings_url, 'GET')
        if headers.status != 200: raise Exception('Settings listing failed - %s, %s' %
                                                 (headers,response))
        dom = XML(response)
        sections = ['settings', 'jai','coverageAccess']
        for section in sections:
            params = []
            node = dom.find(section)
            if node is not None: #it will be none if the catalog does not support this operation
                for entry in node:
                    if len(entry) == 0:
                        params.append((entry.tag, entry.text))
                    else:
                        for subentry in entry:
                            params.append((entry.tag + '/' + subentry.tag, subentry.text))
                settings[section] = params

        return settings

    def update(self, settings):
        root = ET.Element('global')
        for section in settings:
            params = settings[section]
            element = ET.SubElement(root, section)
            for name, value in params:
                if '/' in name:
                    name, subname = name.split('/')
                    subelement = element.find(name)
                    if subelement is None:
                        subelement = ET.SubElement(element, name)
                    subsubelement = ET.SubElement(subelement, subname)
                    subsubelement.text = unicode(value)
                else:
                    subelement = ET.SubElement(element, name)
                    subelement.text = unicode(value)

        xml = ET.tostring(root)
        settings_url = url(self.catalog.service_url, ['settings.xml'])
        headers = {'Content-type': 'text/xml'}
        headers, response = self.http.request(settings_url, 'PUT', xml, headers = headers)
        if headers.status != 200: raise Exception('Settings update failed - %s, %s' %
                                                 (headers,response))
