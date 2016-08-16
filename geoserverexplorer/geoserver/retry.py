# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
from .basecatalog import BaseCatalog
import httplib2
from urlparse import urlparse

def retryMethodDecorator(func):
    def decorator(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except Exception, e:
            if "Errno 10053" in unicode(e):
                result = func(*args, **kwargs)
            else:
                raise e
        return result
    return decorator

class RetryCatalog(BaseCatalog):

    def setup_connection(self):
        self.http = RetryConnection(
            disable_ssl_certificate_validation=self.disable_ssl_cert_validation)
        self.http.add_credentials(self.username, self.password)
        netloc = urlparse(self.service_url).netloc
        self.http.authorizations.append(
            httplib2.BasicAuthentication(
                (self.username, self.password),
                netloc,
                self.service_url,
                {},
                None,
                None,
                self.http
            ))


class RetryConnection(httplib2.Http):
    def __getattribute__(self, attr_name):
        obj = super(httplib2.Http, self).__getattribute__(attr_name)
        if hasattr(obj, '__call__') and hasattr(obj, '__name__'):
            if not obj.__name__.startswith('__'):
                return retryMethodDecorator(obj)
        return obj
