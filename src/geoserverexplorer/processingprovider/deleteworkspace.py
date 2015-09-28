from qgis.core import *
from geoserveralgorithm import GeoServerAlgorithm
from processing.core.parameters import *


class DeleteWorkspace(GeoServerAlgorithm):

    WORKSPACE = 'WORKSPACE'

    def processAlgorithm(self, progress):
        self.createCatalog()
        workspaceName = self.getParameterValue(self.WORKSPACE)
        ws = self.catalog.get_workspace(workspaceName)
        self.catalog.delete(ws)

    def defineCharacteristics(self):
        self.addBaseParameters()
        self.name = 'Delete workspace'
        self.group = 'GeoServer tools'
        self.addParameter(ParameterString(self.WORKSPACE, 'Workspace'))
