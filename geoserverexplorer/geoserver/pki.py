# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
from .basecatalog import BaseCatalog
import httplib2
from gsimporter.client import Client, _Client
from qgis.core import QGis

class PKICatalog(BaseCatalog):

    def __init__(self, service_url, key, cert, ca_cert):
        assert QGis.QGIS_VERSION_INT < 21200, "For QGIS > 2.12 we want to use AuthCatalog!"
        self.key = key
        self.cert = cert
        self.service_url = service_url
        if self.service_url.endswith("/"):
            self.service_url = self.service_url.strip("/")
        self.ca_cert = ca_cert
        self.http = httplib2.Http(ca_certs=self.ca_cert, disable_ssl_certificate_validation=False)
        self.http.add_certificate(key, cert, '')
        self._cache = dict()
        self._version = None

class PKIClient(Client):

    def __init__(self, url, key, cert, ca_cert):
        self.client = _PKIClient(url, key, cert, ca_cert)

    def __getstate__(self):
        cl = self.client
        return {'url':cl.service_url,'keyfile':cl.key,'certfile':cl.cert, 'cafile':cl.ca_cert}
    def __setstate__(self,state):
        self.client = _PKIClient(state['url'],state['keyfile'],state['certfile'], state['cafile'])

class _PKIClient(_Client):

    def __init__(self, url, key, cert, ca_cert):
        self.service_url = url
        if self.service_url.endswith("/"):
            self.service_url = self.service_url.strip("/")
        self.ca_cert = ca_cert
        self.http = httplib2.Http(ca_certs = self.ca_cert, disable_ssl_certificate_validation = False)
        self.http.add_certificate(key, cert, '')
