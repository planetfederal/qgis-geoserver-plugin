# -*- coding: utf-8 -*-
"""
***************************************************************************
    An httplib2 replacement that uses QgsNetworkAccessManager

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

from PyQt4.QtCore import QUrl
from PyQt4.QtCore import pyqtSlot, QEventLoop
from PyQt4.QtNetwork import *
from qgis.core import QgsNetworkAccessManager, QgsAuthManager, QgsMessageLog
from geoserver.catalog import FailedRequestError


# FIXME: ignored
DEFAULT_MAX_REDIRECTS = 4

class RequestsExceptionsTimeout(Exception):
    pass

class RequestsExceptionsConnectionError(Exception):
    pass

class Map(dict):
    """
    Example:
    m = Map({'first_name': 'Eduardo'}, last_name='Pool', age=24, sports=['Soccer'])
    """
    def __init__(self, *args, **kwargs):
        super(Map, self).__init__(*args, **kwargs)
        for arg in args:
            if isinstance(arg, dict):
                for k, v in arg.iteritems():
                    self[k] = v

        if kwargs:
            for k, v in kwargs.iteritems():
                self[k] = v

    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __setitem__(self, key, value):
        super(Map, self).__setitem__(key, value)
        self.__dict__.update({key: value})

    def __delattr__(self, item):
        self.__delitem__(item)

    def __delitem__(self, key):
        super(Map, self).__delitem__(key)
        del self.__dict__[key]


class Response(Map):
    pass

class NetworkAccessManager():
    """
    This class mimicks httplib2 by using QgsNetworkAccessManager for all
    network calls.

    The return value is a tuple of (response, content), the first being and
    instance of the Response class, the second being a string that contains
    the response entity body.
    """

    def __init__(self, authid=None, disable_ssl_certificate_validation=False, debug=True, raise_exceptions=False):
        self.disable_ssl_certificate_validation = disable_ssl_certificate_validation
        self.authid = authid
        self.reply = None
        self.debug = debug
        self.raise_exceptions = raise_exceptions

    def msg_log(self, msg):
        QgsMessageLog.logMessage(msg, "NetworkAccessManager")

    def request(self, url, method="GET", body=None, headers=None, redirections=DEFAULT_MAX_REDIRECTS, connection_type=None):
        self.msg_log(u'http_call request: {0}'.format(url))
        self.http_call_result = Response({
            'status': 0,
            'status_code': 0,
            'status_message': '',
            'text' : '',
            'ok': False,
            'headers': {},
            'reason': '',
        })
        req = QNetworkRequest()
        req.setUrl(QUrl(url))
        if headers is not None:
            for k, v in headers.items():
                req.setRawHeader(k, v)
        if self.authid:
            QgsAuthManager.instance().updateNetworkRequest(req, self.authid)
        if self.reply is not None and self.reply.isRunning():
            self.reply.close()
        if method.lower() == 'delete':
            func = getattr(QgsNetworkAccessManager.instance(), 'deleteResource')
        else:
            func = getattr(QgsNetworkAccessManager.instance(), method.lower())
        # Calling the server ...
        # Let's log the whole call for debugging purposes:
        if self.debug:
            self.msg_log("Sending %s request to %s" % (method.upper(), req.url().toString()))
            headers = {str(h): str(req.rawHeader(h)) for h in req.rawHeaderList()}
            for k, v in headers.items():
                self.msg_log("%s: %s" % (k, v))
        if method.lower() in ['post', 'put']:
            if isinstance(body, file):
                body = body.read()
            self.reply = func(req, body)
        else:
            self.reply = func(req)
        if self.authid:
            self.msg_log("update reply w/ authid: {0}".format(self.authid))
            QgsAuthManager.instance().updateNetworkReply(self.reply, self.authid)

        self.reply.finished.connect(self.replyFinished)

        # Call and block
        self.el = QEventLoop()
        self.reply.finished.connect(self.el.quit)

        # Catch all exceptions (and clean up requests)
        try:
            self.el.exec_()
            # Let's log the whole response for debugging purposes:
            if self.debug:
                self.msg_log("Got response %s %s from %s" % \
                            (self.http_call_result.status_code,
                             self.http_call_result.status_message,
                             self.reply.url().toString()))
                headers = {str(h): str(self.reply.rawHeader(h)) for h in self.reply.rawHeaderList()}
                for k, v in headers.items():
                    self.msg_log("%s: %s" % (k, v))
                if len(self.http_call_result.text) < 1024:
                    self.msg_log("Payload :\n%s" % self.http_call_result.text)
                else:
                    self.msg_log("Payload is > 1 KB ...")
        except Exception, e:
            raise e
        finally:
            self.reply.close()
            self.msg_log("Deleting reply ...")
            self.reply.deleteLater()
            self.reply = None
        if not self.http_call_result.ok:
            raise FailedRequestError(self.http_call_result.reason)
        return (self.http_call_result, self.http_call_result.text)

    @pyqtSlot()
    def replyFinished(self):
        err = self.reply.error()
        httpStatus = self.reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        httpStatusMessage = self.reply.attribute(QNetworkRequest.HttpReasonPhraseAttribute)
        self.http_call_result.status_code = httpStatus
        self.http_call_result.status = httpStatus
        self.http_call_result.status_message = httpStatusMessage
        for k, v in self.reply.rawHeaderPairs():
            self.http_call_result.headers[str(k)] = str(v)
            self.http_call_result.headers[str(k).lower()] = str(v)
        if err != QNetworkReply.NoError:
            msg = "Network error #{0}: {1}".format(
                self.reply.error(), self.reply.errorString())
            self.http_call_result.reason = msg
            self.http_call_result.ok = False
            self.msg_log(msg)
            if self.raise_exceptions:
                if err == QNetworkReply.TimeoutError:
                    raise RequestsExceptionsTimeout(msg)
                if err == QNetworkReply.ConnectionRefusedError:
                    raise RequestsExceptionsConnectionError(msg)
                else:
                    raise Exception(msg)
            else:
                self.http_call_result.ok = False
                self.http_call_result.reason = msg
        else:
            self.http_call_result.text = str(self.reply.readAll())
            self.http_call_result.ok = True
