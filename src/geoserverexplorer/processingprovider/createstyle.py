
from qgis.core import *
from geoserveralgorithm import GeoServerAlgorithm
from processing.parameters.ParameterString import ParameterString
from processing.parameters.ParameterFile import ParameterFile
from processing.parameters.ParameterBoolean import ParameterBoolean


class CreateStyle(GeoServerAlgorithm):

    STYLE = 'STYLE'
    OVERWRITE = 'OVERWRITE'
    NAME = 'NAME'

    def processAlgorithm(self, progress):
        self.createCatalog()
        stylefile = self.getParameterValue(self.STYLE)
        overwrite = self.getParameterValue(self.OVERWRITE)
        name = self.getParameterValue(self.NAME)
        self.catalog.create_style(name, stylefile, overwrite)

    def defineCharacteristics(self):
        self.addBaseParameters()
        self.name = 'Add style'
        self.group = 'GeoServer tools'
        self.addParameter(ParameterString(self.NAME, 'Style name'))
        self.addParameter(ParameterFile(self.STYLE, 'Style SLD file'))
        self.addParameter(ParameterBoolean(self.OVERWRITE, 'Overwrite'))
