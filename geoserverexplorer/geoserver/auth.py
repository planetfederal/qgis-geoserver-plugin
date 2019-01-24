# -*- coding: utf-8 -*-

"""
***************************************************************************
    A catalog that uses QgsNetworkAccessManager
    ---------------------
    Date                 : August 2016
    Copyright            : (C) 2016 Boundless, http://boundlessgeo.com
    Email                : apasotti at boundlessgeo dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'Alessandro Pasotti'
__date__ = 'August 2016'

from datetime import timedelta, datetime
from xml.etree.ElementTree import XML
from xml.parsers.expat import ExpatError
from geoserver.catalog import FailedRequestError
from qgiscommons2.network.networkaccessmanager import NetworkAccessManager
from .basecatalog import BaseCatalog

class AuthCatalog(BaseCatalog):

    def __init__(self, service_url, authid, cache_time):
        # Do not call parent constructor, this is a patching class
        self.authid = authid
        self.cache_time = cache_time
        self.service_url = service_url.strip("/")
        self._cache = dict()
        self._version = None
        self.nam = NetworkAccessManager(self.authid, exception_class=FailedRequestError, debug=False)
        self.username = ''
        self.password = ''

    def http_request(self, url, data=None, method='get', headers = {}):
        resp, content = self.nam.request(url, method, data, headers)
        return resp

    def setup_connection(self):
        pass



