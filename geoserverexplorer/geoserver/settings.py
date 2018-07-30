# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#

from builtins import str
from builtins import object
import httplib2
from xml.etree.ElementTree import XML
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from geoserver.support import build_url
from geoserverexplorer.geoserver.auth import AuthCatalog

class Settings(object):

    def __init__(self, catalog):
        self.catalog = catalog

    def settings(self):
        settings = {}
        settings_url = build_url(self.catalog.service_url, ['settings.xml'])
        resp = self.catalog.http_request(settings_url, 'GET')
        if resp.status_code != 200: 
            raise Exception('Settings listing failed: ' + resp.text)
        dom = XML(resp.text)
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
                    subsubelement.text = str(value)
                else:
                    subelement = ET.SubElement(element, name)
                    subelement.text = str(value)

        xml = ET.tostring(root)
        settings_url = build_url(self.catalog.service_url, ['settings.xml'])
        headers = {'Content-type': 'text/xml'}
        resp = self.catalog.http_request(settings_url, xml, 'PUT', headers = headers)
        if resp.status_code != 200: 
            raise Exception('Settings update failed: ' + resp.text)
