import os
from PyQt4 import QtGui
from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterString
from geoserver.catalog import Catalog


class GeoServerAlgorithm(GeoAlgorithm):

    URL = 'URL'
    USER = 'USER'
    PASSWORD = 'PASSWORD'

    def getIcon(self):
        return QtGui.QIcon(os.path.dirname(__file__)
                           + '/../images/geoserver.png')

    def addBaseParameters(self):
        self.addParameter(ParameterString(self.URL, 'URL',
                          'http://localhost:8080/geoserver/rest'))
        self.addParameter(ParameterString(self.USER, 'User', 'admin'))
        self.addParameter(ParameterString(self.PASSWORD, 'Password',
                          'geoserver'))

    def createCatalog(self):
        url = self.getParameterValue(self.URL)
        user = self.getParameterValue(self.USER)
        password = self.getParameterValue(self.PASSWORD)
        self.catalog = Catalog(url, user, password)
