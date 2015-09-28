
import os
from PyQt4.QtGui import QIcon
from processing.core.AlgorithmProvider import AlgorithmProvider
from processing.core.ProcessingConfig import Setting, ProcessingConfig
from uploadvector import UploadVector
from uploadraster import UploadRaster
from createstyle import CreateStyle
from createworkspace import CreateWorkspace
from deleteworkspace import DeleteWorkspace
from deletedatastore import DeleteDatastore

class GeoServerProvider(AlgorithmProvider):

    MY_DUMMY_SETTING = 'MY_DUMMY_SETTING'

    def __init__(self):
        AlgorithmProvider.__init__(self)

        self.activate = True

        # Load algorithms
        self.alglist = [
            UploadVector(),
            UploadRaster(),
            CreateWorkspace(),
            DeleteWorkspace(),
            DeleteDatastore(),
            CreateStyle(),
            ]
        for alg in self.alglist:
            alg.provider = self

    def initializeSettings(self):
        AlgorithmProvider.initializeSettings(self)


    def unload(self):
        AlgorithmProvider.unload(self)


    def getName(self):
        return 'geoserver'

    def getDescription(self):
        return 'GeoServer tools'

    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + "/../images/geoserver.png")

    def _loadAlgorithms(self):
        self.algs = self.alglist
