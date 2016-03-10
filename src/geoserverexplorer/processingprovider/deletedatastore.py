# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
from qgis.core import *
from geoserveralgorithm import GeoServerAlgorithm
from processing.core.parameters import *


class DeleteDatastore(GeoServerAlgorithm):

    DATASTORE = 'DATASTORE'
    WORKSPACE = 'WORKSPACE'

    def processAlgorithm(self, progress):
        self.createCatalog()
        datastoreName = self.getParameterValue(self.DATASTORE)
        workspaceName = self.getParameterValue(self.WORKSPACE)
        ds = self.catalog.get_store(datastoreName, workspaceName)
        self.catalog.delete(ds, recurse=True)

    def defineCharacteristics(self):
        self.addBaseParameters()
        self.name = 'Delete datastore'
        self.group = 'GeoServer tools'
        self.addParameter(ParameterString(self.DATASTORE, 'Datastore name'))
        self.addParameter(ParameterString(self.WORKSPACE, 'Workspace'))
