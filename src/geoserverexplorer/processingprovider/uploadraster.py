# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
from qgis.core import *
from geoserveralgorithm import GeoServerAlgorithm
from processing.core.parameters import *


class UploadRaster(GeoServerAlgorithm):

    INPUT = 'INPUT'
    WORKSPACE = 'WORKSPACE'
    NAME = 'NAME'

    def exportRasterLayer(self, inputFilename):
        return inputFilename

    def processAlgorithm(self, progress):
        self.createCatalog()
        inputFilename = self.getParameterValue(self.INPUT)
        name = self.getParameterValue(self.NAME)
        workspaceName = self.getParameterValue(self.WORKSPACE)
        filename = self.exportRasterLayer(inputFilename)
        workspace = self.catalog.get_workspace(workspaceName)
        ds = self.catalog.create_coveragestore2(name, workspace)
        ds.data_url = 'file:' + filename
        self.catalog.save(ds)

    def defineCharacteristics(self):
        self.addBaseParameters()
        self.name = 'Upload raster'
        self.group = 'GeoServer tools'
        self.addParameter(ParameterRaster(self.INPUT, 'Layer to import'))
        self.addParameter(ParameterString(self.WORKSPACE, 'Workspace'))
        self.addParameter(ParameterString(self.NAME, 'Store name'))
