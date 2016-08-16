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
import logging
from xml.etree.ElementTree import XML
from xml.parsers.expat import ExpatError
from geoserver.catalog import FailedRequestError
from gsimporter.client import Client, _Client
from .networkaccessmanager import NetworkAccessManager
from .basecatalog import BaseCatalog

logger = logging.getLogger("auth.authcatalog")

class AuthCatalog(BaseCatalog):

    def __init__(self, service_url, authid, cache_time):
        # Do not call parent constructor, this is a patching class
        self.authid = authid
        self.cache_time = cache_time
        self.service_url = service_url
        self._cache = dict()
        self._version = None
        self.http = NetworkAccessManager(self.authid, exception_class=FailedRequestError)
        self.username = ''
        self.password = ''

    def setup_connection(self):
        pass

    def get_xml(self, rest_url):
        """Read cached time from settings"""
        logger.debug("GET %s", rest_url)

        cached_response = self._cache.get(rest_url)

        def is_valid(cached_response):
            return cached_response is not None and datetime.now() - cached_response[0] < timedelta(seconds=self.cache_time)

        def parse_or_raise(xml):
            try:
                return XML(xml)
            except (ExpatError, SyntaxError), e:
                msg = "GeoServer gave non-XML response for [GET %s]: %s"
                msg = msg % (rest_url, xml)
                raise Exception(msg, e)

        if is_valid(cached_response):
            raw_text = cached_response[1]
            return parse_or_raise(raw_text)
        else:
            response, content = self.http.request(rest_url)
            if response.status == 200:
                self._cache[rest_url] = (datetime.now(), content)
                return parse_or_raise(content)
            else:
                raise FailedRequestError("Tried to make a GET request to %s but got a %d status code: \n%s" % (rest_url, response.status, content))


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
