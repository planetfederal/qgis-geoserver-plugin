# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
class GeoserverException(Exception):
    def __init__(self, message, details=None):
        super().__init__(message)
        self.details = details
