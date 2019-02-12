# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#

from builtins import str
from builtins import range
import os
import re
import tempfile
import unittest
from geoserver.util import shapefile_and_friends
from geoserverexplorer.qgis.catalog import createGeoServerCatalog

from qgis.core import (QgsProject,
                       QgsAuthManager,
                       QgsAuthMethodConfig,
                       QgsAuthCertUtils,
                       QgsDataSourceUri)
import qgis
import geoserverexplorer
from geoserverexplorer.gui.gsexploreritems import *
from qgis.PyQt.QtNetwork import QSslCertificate, QSslKey, QSsl

PREFIX = "qgis_plugin_test_"

def safeName(name):
    return PREFIX + name

REFERENCE_LAYER = "reference_layer"
PT1 = safeName("pt1")
PT1JSON = safeName("pt1json")
PT2 = safeName("pt2")
PT3 = safeName("pt3")
DEM = safeName("dem")
DEM2 = safeName("dem2")
DEMASCII = safeName("demascii")
GEOLOGY_GROUP = safeName("geology_landuse")
GEOFORMS = safeName("geoforms")
LANDUSE = safeName("landuse")
GROUP = safeName("group")
STYLE = safeName("style")
HOOK = safeName("hook")
WORKSPACE = safeName("workspace")
WORKSPACEB = safeName("workspaceb")

# envs that can be override by os.environ envs
GSHOSTNAME = 'localhost'
GSPORT = '8080'
GSUSER = 'admin'
GSPASSWORD = 'geoserver'

AUTHDB_MASTERPWD = 'password'
AUTHCFGID = "geoservertest"

USEAUTHSYSTEM = False

AUTHDBDIR = tempfile.mkdtemp(prefix='tmp-qgis_authdb',
                             dir=tempfile.gettempdir())

def getGeoServerCatalog():
    authid = AUTHCFGID if USEAUTHSYSTEM else None
    conf = dict(
        URL=serverLocationBasicAuth()+'/rest',
        USER=GSUSER,
        PASSWORD=GSPASSWORD,
        AUTHCFG=authid)

    conf.update([(k, os.getenv('GS%s' % k))
                for k in conf if 'GS%s' % k in os.environ])
    cat = createGeoServerCatalog(conf['URL'], conf['USER'], conf['PASSWORD'],
                                 conf['AUTHCFG'])
    try:
        cat.catalog.gsversion()
    except Exception as ex:
        msg = 'cannot reach geoserver using provided credentials %s, msg is %s'
        raise AssertionError(msg % (conf, ex))
    return cat


def cleanCatalog(cat):
    for groupName in [GROUP, GEOLOGY_GROUP]:
        def _del_group(groupName, cat):
            groups = cat.get_layergroups(groupName)
            if groups:
                cat.delete(groups[0])
                groups = cat.get_layergroups(groupName)
                assert groups == []

        _del_group(groupName, cat)
        # Try with namespaced
        _del_group("%s:%s" % (WORKSPACE, groupName), cat)

    toDelete = []
    for layer in cat.get_layers():
        if layer.name.startswith(PREFIX):
            toDelete.append(layer)
    for style in cat.get_styles():
        if style.name.startswith(PREFIX):
            toDelete.append(style)

    for e in toDelete:
        try:
            cat.delete(e, purge=True)
        except:
            pass

    for ws in cat.get_workspaces():
        if not ws.name.startswith(PREFIX):
            continue
        if ws is not None:
            for store in cat.get_stores(workspaces=ws):
                for resource in store.get_resources():
                    try:
                        cat.delete(resource)
                    except:
                        pass
                cat.delete(store)
            cat.delete(ws)
            ws = cat.get_workspaces(ws.name)
            assert len(ws) == 0


def populateCatalog(cat):
    cleanCatalog(cat)
    cat.create_workspace(WORKSPACE, "http://test.com")
    ws = cat.get_workspaces(WORKSPACE)[0]
    path = os.path.join(os.path.dirname(__file__), "data", PT2)
    data = shapefile_and_friends(path)
    cat.create_featurestore(PT2, data, ws)
    path = os.path.join(os.path.dirname(__file__), "data", PT3)
    data = shapefile_and_friends(path)
    cat.create_featurestore(PT3, data, ws)
    sldfile = os.path.join(os.path.dirname(__file__),
                           "resources", "vector.sld")
    with open(sldfile, 'r') as f:
        sld = f.read()
    cat.create_style(STYLE, sld, True)
    group = cat.create_layergroup(GROUP, [PT2])
    cat.save(group)
    cat.create_workspace(WORKSPACEB, "http://testb.com")
    cat.set_default_workspace(WORKSPACE)


def geoserverLocation():
    host = os.getenv("GSHOSTNAME", GSHOSTNAME)
    port = os.getenv("GSPORT", GSPORT)
    return '%s:%s' % (host, port)


def geoserverLocationSsh():
    host = os.getenv("GSHOSTNAME", GSHOSTNAME)
    port = os.getenv("GSSSHPORT", GSSSHPORT)
    return '%s:%s' % (host, port)


def serverLocationBasicAuth():
    url = geoserverLocation() + "/geoserver"
    if not geoserverLocation().startswith("http"):
        url = "http://" + url
    return url


#######################################################################
#     Auth config utils
#######################################################################

def disableAuth():
    global USEAUTHSYSTEM
    USEAUTHSYSTEM = False
    
def enableAuth():
    initAuthManager()
    initAuthConfigId()
    global USEAUTHSYSTEM
    USEAUTHSYSTEM = True

def initAuthManager():
    return
    """
    Setup AuthManager instance.

    heavily based on testqgsauthmanager.cpp.
    """    
    am = QgsApplication.authManager()
    # check if QgsAuthManager has been already initialised... a side effect
    # of the QgsAuthManager.init() is that AuthDbPath is set
    if am.authenticationDbPath():
        # already initilised => we are inside QGIS. Assumed that the
        # actual qgis_auth.db has the same master pwd as AUTHDB_MASTERPWD
        if am.masterPasswordIsSet():
            msg = 'Auth master password not set from passed string'
            assert am.masterPasswordSame(AUTHDB_MASTERPWD)
        else:
            msg = 'Master password could not be set'
            assert am.setMasterPassword(AUTHDB_MASTERPWD, True), msg
    else:
        # outside qgis => setup env var before db init
        os.environ['QGIS_AUTH_DB_DIR_PATH'] = AUTHDBDIR
        msg = 'Master password could not be set'
        assert am.setMasterPassword(AUTHDB_MASTERPWD, True), msg
        am.init(AUTHDBDIR)

def initAuthConfigId():
    am =  QgsApplication.authManager()
    if AUTHCFGID not in am.configIds():
        conf = dict(
            URL=serverLocationBasicAuth()+'/rest',
            USER=GSUSER,
            PASSWORD=GSPASSWORD,
            AUTHCFG=AUTHCFGID)

        conf.update([(k, os.getenv('GS%s' % k))
                for k in conf if 'GS%s' % k in os.environ])

        cfg = QgsAuthMethodConfig()
        cfg.setId(AUTHCFGID)
        cfg.setName('Geoserver test')
        cfg.setMethod('Basic')
        cfg.setConfig('username', conf['USER'])
        cfg.setConfig('password', conf['PASSWORD'])
        am.storeAuthenticationConfig(cfg)


#######################################################################
#     Functional test utils
#######################################################################

# Some common methods
def loadTestData():
    curPath = os.path.dirname(os.path.abspath(geoserverexplorer.__file__))
    projectFile = os.path.join(curPath, "test", "data", "test.qgs")
    qgis.utils.iface.addProject(projectFile)


def loadSymbologyTestData():
    curPath = os.path.dirname(os.path.abspath(geoserverexplorer.__file__))
    projectFile = os.path.join(curPath, "test", "data",
                               "symbology", "test.qgs")
    qgis.utils.iface.addProject(projectFile)


def getCatalog():
    catWrapper = getGeoServerCatalog()
    return catWrapper

def setUpCatalogAndWorkspace():
    catWrapper = getCatalog()
    try:
        clean()
    except:
        raise
    catWrapper.catalog.create_workspace("test_workspace", "http://test.com")
    return catWrapper


def setUpCatalogAndExplorer():
    explorer = qgis.utils.plugins["geoserverexplorer"].explorer
    explorer.show()
    gsItem = explorer.explorerTree.gsItem
    for c in range(gsItem.childCount()):
        gsItem.removeChild(gsItem.child(c))
    catWrapper = setUpCatalogAndWorkspace()
    geoserverItem = GsCatalogItem(catWrapper.catalog, "test_catalog")
    gsItem.addChild(geoserverItem)
    geoserverItem.populate()
    gsItem.setExpanded(True)

# TESTS

def checkNewLayer():
    cat = getCatalog().catalog
    stores = cat.get_stores(WORKSPACE)
    assert len(stores) != 0


def clean():
    global AUTHM
    cat = getCatalog().catalog
    ws = cat.get_workspaces(WORKSPACE)
    if ws:
        cat.delete(ws[0], recurse=True)
        ws = cat.get_workspaces(ws[0].name)
        assert len(ws) == 0

def testProjects():
    curPath = os.path.dirname(os.path.abspath(geoserverexplorer.__file__))
    projectFolder = os.path.join(curPath, "test", "data", "symbology")
    projects = [os.path.join(projectFolder, p) for p in os.listdir(projectFolder) if p.endswith(".qgs")]
    return projects

def openAndUpload(projectFile):
    global AUTHCFGID
    qgis.utils.iface.addProject(projectFile)
    layer = layerFromName(REFERENCE_LAYER)
    catWrapper = setUpCatalogAndWorkspace()
    cat = catWrapper.catalog
    catWrapper.publishLayer(layer, "test_workspace", True)
    stores = cat.get_stores(workspaces = "test_workspace")
    #assert len(stores) != 0
    catWrapper.addLayerToProject(REFERENCE_LAYER, "WFS")
    url = "crs=EPSG:4326&format=image/png&layers=test_workspace:reference_layer&styles=reference_layer&url=%s/wms" % serverLocationBasicAuth()
    wmsLayer = QgsRasterLayer(url, "WMS", 'wms')
    assert wmsLayer.isValid()
    QgsProject.instance().addMapLayer(wmsLayer)
    qgis.utils.iface.zoomToActiveLayer()


def layerFromName(name):
    '''
    Returns the layer from the current project with the passed name
    Returns None if no layer with that name is found
    If several layers with that name exist, only the first one is returned
    '''
    layers = list(QgsProject.instance().mapLayers().values())
    for layer in layers:
        if layer.name() == name:
            return layer


class UtilsTestCase(unittest.TestCase):

    RE_ATTRIBUTES = '[^>\s]+=[^>\s]+'

    def assertXMLEqual(self, response, expected, msg=''):
        """Compare XML line by line and sorted attributes"""
        # Ensure we have newlines
        if response.count('\n') < 2:
            response = re.sub('(</[^>]+>)', '\\1\n', response)
            expected = re.sub('(</[^>]+>)', '\\1\n', expected)
        response_lines = response.splitlines()
        expected_lines = expected.splitlines()
        line_no = 1
        for expected_line in expected_lines:
            expected_line = expected_line.strip()
            response_line = response_lines[line_no - 1].strip()
            # Compare tag
            try:
                self.assertEqual(re.findall('<([^>\s]+)[ >]', expected_line)[0],
                                 re.findall('<([^>\s]+)[ >]', response_line)[0], msg=msg + "\nTag mismatch on line %s: %s != %s" % (line_no, expected_line, response_line))
            except IndexError:
                self.assertEqual(expected_line, response_line, msg=msg + "\nTag line mismatch %s: %s != %s" % (line_no, expected_line, response_line))
            #print("---->%s\t%s == %s" % (line_no, expected_line, response_line))
            # Compare attributes
            if re.match(self.RE_ATTRIBUTES, expected_line): # has attrs
                expected_attrs = re.findall(self.RE_ATTRIBUTES, expected_line)
                expected_attrs.sort()
                response_attrs = re.findall(self.RE_ATTRIBUTES, response_line)
                response_attrs.sort()
                self.assertEqual(expected_attrs, response_attrs, msg=msg + "\nXML attributes differ at line {0}: {1} != {2}".format(line_no, expected_attrs, response_attrs))
            line_no += 1
