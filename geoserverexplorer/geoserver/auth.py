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

from geoserver.catalog import Catalog
from gsimporter.client import Client, _Client
from .networkaccessmanager import NetworkAccessManager
from geoserver.catalog import FailedRequestError

class AuthCatalog(Catalog):

    def __init__(self, service_url, authid):
        self.authid = authid
        self.service_url = service_url
        self._cache = dict()
        self._version = None
        self.http = NetworkAccessManager(self.authid, exception_class=FailedRequestError)
        self.username = ''
        self.password = ''

    def setup_connection(self):
        pass


class AuthClient(Client):

    def __init__(self, url, authid):
        self.client = _AuthClient(url, authid)

    def __getstate__(self):
        cl = self.client
        return {'url':cl.service_url, 'authid': cl.authid}
    def __setstate__(self,state):
        self.client = _AuthClient(state['url'], state['authid'])


class _AuthClient(_Client):

    def __init__(self, url, authid):
        self.service_url = url
        self.authid = authid
        if self.service_url.endswith("/"):
            self.service_url = self.service_url.strip("/")
        self.http = NetworkAccessManager(self.authid, exception_class=FailedRequestError)
