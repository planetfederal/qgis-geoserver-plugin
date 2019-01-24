# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
from builtins import str
 
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *

from qgis.gui import *
from qgis.core import *
from geoserverexplorer.geoserver.auth import AuthCatalog

class DefineCatalogDialog(QDialog):

    def __init__(self, catalogs, parent=None, catalog=None, name=None):
        super(DefineCatalogDialog, self).__init__(parent)
        self.catalogs = catalogs
        self.ok = False
        self.catalog = catalog
        self.name = name
        self.initGui()

    def initGui(self):

        authid = None
        if self.name is not None:
            if self.catalog is None:
                settings = QSettings()
                settings.beginGroup("/GeoServer/Catalogs/" + self.name)
                url = str(settings.value("url"))
                username = settings.value("username")
                authid = settings.value("authid")
                settings.endGroup()
            elif isinstance(self.catalog, AuthCatalog):
                settings = QSettings()
                settings.beginGroup("/GeoServer/Catalogs/" + self.name)
                username = ""
                authid = self.catalog.authid
                url = self.catalog.service_url
                settings.endGroup()            
            else:
                username = self.catalog.username
                url = self.catalog.service_url
        else:
            settings = QSettings()
            username = ""
            url = settings.value('/GeoServer/LastCatalogUrl', 'http://localhost:8080/geoserver')

        if url.endswith("/rest"):
            url = url[:-5]

        self.setWindowTitle('Catalog definition')

        verticalLayout = QVBoxLayout()

        horizontalLayout = QHBoxLayout()
        horizontalLayout.setSpacing(30)
        horizontalLayout.setMargin(0)
        nameLabel = QLabel('Catalog name')
        nameLabel.setMinimumWidth(150)
        self.nameBox = QLineEdit()
        settings = QSettings()
        name = self.name or settings.value('/GeoServer/LastCatalogName', 'Default GeoServer catalog')
        self.nameBox.setText(name)

        self.nameBox.setMinimumWidth(250)
        horizontalLayout.addWidget(nameLabel)
        horizontalLayout.addWidget(self.nameBox)
        verticalLayout.addLayout(horizontalLayout)

        horizontalLayout = QHBoxLayout()
        horizontalLayout.setSpacing(30)
        horizontalLayout.setMargin(0)
        urlLabel = QLabel('URL')
        urlLabel.setMinimumWidth(150)
        self.urlBox = QLineEdit()

        self.urlBox.setText(url)
        self.urlBox.setMinimumWidth(250)
        horizontalLayout.addWidget(urlLabel)
        horizontalLayout.addWidget(self.urlBox)
        verticalLayout.addLayout(horizontalLayout)

        self.groupBox = QGroupBox()
        self.groupBox.setTitle("GeoServer Connection parameters")
        self.groupBox.setLayout(verticalLayout)

        layout = QVBoxLayout()
        layout.addWidget(self.groupBox)
        self.spacer = QSpacerItem(20,20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(self.spacer)

        self.tabWidget = QTabWidget()

        tabBasicAuth = QWidget()
        tabBasicAuthLayout = QVBoxLayout(tabBasicAuth)

        horizontalLayout = QHBoxLayout()
        horizontalLayout.setSpacing(30)
        horizontalLayout.setMargin(0)
        usernameLabel = QLabel('User name')
        usernameLabel.setMinimumWidth(150)
        self.usernameBox = QLineEdit()
        self.usernameBox.setText(username)
        self.usernameBox.setMinimumWidth(250)
        self.usernameBox.setText(username)
        horizontalLayout.addWidget(usernameLabel)
        horizontalLayout.addWidget(self.usernameBox)
        tabBasicAuthLayout.addLayout(horizontalLayout)

        horizontalLayout = QHBoxLayout()
        horizontalLayout.setSpacing(30)
        horizontalLayout.setMargin(0)
        passwordLabel = QLabel('Password')
        passwordLabel.setMinimumWidth(150)
        self.passwordBox = QLineEdit()
        self.passwordBox.setEchoMode(QLineEdit.Password)
        self.passwordBox.setMinimumWidth(250)
        horizontalLayout.addWidget(passwordLabel)
        horizontalLayout.addWidget(self.passwordBox)
        tabBasicAuthLayout.addLayout(horizontalLayout)

        self.tabWidget.addTab(tabBasicAuth, "Basic")

        self.certWidget = QgsAuthConfigSelect()
        if authid is not None:
            self.certWidget.setConfigId(authid)
        self.tabWidget.addTab(self.certWidget, "Configurations")

        verticalLayout3 = QVBoxLayout()
        verticalLayout3.addWidget(self.tabWidget)

        self.authBox = QGroupBox()
        self.authBox.setTitle("Authentication")
        self.authBox.setLayout(verticalLayout3)

        verticalLayout.addWidget(self.authBox)

        if self.catalog is not None:
            if isinstance(self.catalog, AuthCatalog):
                self.tabWidget.setCurrentIndex(1)
            else:
                self.tabWidget.setCurrentIndex(0)
                self.passwordBox.setText(self.catalog.password)
                self.usernameBox.setText(self.catalog.username)
        elif authid is not None:
            self.tabWidget.setCurrentIndex(1)

        self.spacer = QSpacerItem(20,20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(self.spacer)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Close)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)

        self.buttonBox.accepted.connect(self.okPressed)
        self.buttonBox.rejected.connect(self.cancelPressed)

        self.resize(400,200)


    def okPressed(self):
        self.url = str(self.urlBox.text().strip('/') + '/rest')
        if not self.url.startswith('http'):
            self.url = 'http://%s' % self.url
        if self.tabWidget.currentIndex() == 0:
            self.username = str(self.usernameBox.text())
            self.password = str(self.passwordBox.text())
            self.authid = None
        else:
            self.username = None
            self.password = None
            self.authid = self.certWidget.configId()
            authtype = QgsApplication.authManager().configAuthMethodKey(self.authid)
            self.username = ''
            if not authtype or authtype == '':
                QMessageBox.warning(self, "Authentication needed",
                                          "Please specify a valid authentication for connecting to the catalog")
                return

        nametxt = str(self.nameBox.text())
        # increment only when adding a new connection or if editing a saved
        # connection and the name has changed
        if self.name is None or (self.name is not None and nametxt != self.name):
            newname = nametxt
            i = 2
            while newname in list(self.catalogs.keys()):
                newname = nametxt + "_" + str(i)
                i += 1
            self.name = newname
        settings = QSettings()
        settings.setValue('/GeoServer/LastCatalogName', self.nameBox.text())
        settings.setValue('/GeoServer/LastCatalogUrl', self.urlBox.text())
        saveCatalogs = bool(settings.value("/GeoServer/Settings/GeoServer/SaveCatalogs", True, bool))
        if saveCatalogs:
            settings.beginGroup("/GeoServer/Catalogs/" + self.name)
            settings.setValue("url", self.url);
            if self.authid is not None:
                settings.setValue("authid", self.authid)
            else:
                settings.setValue("authid", None)
                settings.setValue("username", self.username)
            settings.endGroup()
        self.ok = True
        self.close()

    def cancelPressed(self):
        self.ok = False
        self.close()
