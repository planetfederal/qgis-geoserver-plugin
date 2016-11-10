# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
import os
import re
import tempfile
import unittest
from geoserver.util import shapefile_and_friends
from geoserverexplorer.qgis.catalog import createGeoServerCatalog

from qgis.core import (QgsMapLayerRegistry,
                       QgsAuthManager,
                       QgsAuthMethodConfig,
                       QgsAuthCertUtils)
import qgis
import geoserverexplorer
from geoserverexplorer.gui.gsexploreritems import *
from PyQt4.QtNetwork import QSslCertificate, QSslKey, QSsl

PREFIX = "qgis_plugin_test_"

def safeName(name):
    return PREFIX + name

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
GSHOSTNAME = 'boundless-test'
GSPORT = '8080'
GSSSHPORT = '8443'
GSUSER = 'admin'
GSPASSWORD = 'geoserver'

# pki envs
AUTHDB_MASTERPWD = 'password'
AUTHCFGID = None
AUTHTYPE = None  # 'Identity-Cert' or "PKI-Paths" or 'PKI-PKCS#12'

# authdb and cert data
AUTH_TESTDATA = os.path.join(os.path.dirname(__file__), "resources",
                             'auth_system')
PKIDATA = os.path.join(AUTH_TESTDATA, 'certs-keys')
AUTHDBDIR = tempfile.mkdtemp(prefix='tmp-qgis_authdb',
                             dir=tempfile.gettempdir())

#
# To avoid revrite some utils methods in PKI context
# has been created a global variable 'AUTHM' that define the running context
#
AUTHM = None

def getGeoServerCatalog(authcfgid=None, authtype=None):
    # beaware that these envs can be overrided by os.environ envs cnaging
    # the function behaviour
    if authcfgid:
        conf = dict(
            URL=serverLocationPkiAuth()+'/rest',
            USER=None,
            PASSWORD=None,
            AUTHCFG=authcfgid,
            AUTHTYPE=authtype
        )
    else:
        conf = dict(
            URL=serverLocationBasicAuth()+'/rest',
            USER=GSUSER,
            PASSWORD=GSPASSWORD,
            AUTHCFG=authcfgid,
            AUTHTYPE=authtype
        )
    conf.update([(k, os.getenv('GS%s' % k))
                for k in conf if 'GS%s' % k in os.environ])
    cat = createGeoServerCatalog(conf['URL'], conf['USER'], conf['PASSWORD'],
                                 conf['AUTHCFG'], conf['AUTHTYPE'])
    try:
        cat.catalog.gsversion()
    except Exception, ex:
        msg = 'cannot reach geoserver using provided credentials %s, msg is %s'
        raise AssertionError(msg % (conf, ex))
    return cat


def cleanCatalog(cat):

    for groupName in [GROUP, GEOLOGY_GROUP]:
        def _del_group(groupName, cat):
            group = cat.get_layergroup(groupName)
            if group is not None:
                cat.delete(group)
                group = cat.get_layergroup(groupName)
                assert group is None

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
            from PyQt4.QtCore import QCoreApplication
            while 1:
                QCoreApplication.instance().processEvents()

    for ws in cat.get_workspaces():
        if not ws.name.startswith(PREFIX):
            continue
        if ws is not None:
            for store in cat.get_stores(ws):
                for resource in store.get_resources():
                    try:
                        cat.delete(resource)
                    except:
                        pass
                cat.delete(store)
            cat.delete(ws)
            ws = cat.get_workspace(ws.name)
            assert ws is None


def populateCatalog(cat):
    cleanCatalog(cat)
    cat.create_workspace(WORKSPACE, "http://test.com")
    ws = cat.get_workspace(WORKSPACE)
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
    server = GSHOSTNAME
    port = GSPORT
    server = os.getenv('GSHOSTNAME', server)
    port = os.getenv('GSPORT', port)
    return '%s:%s' % (server, port)


def geoserverLocationSsh():
    location = geoserverLocation().split(":")[0]
    sshport = GSSSHPORT
    sshport = os.getenv('GSSSHPORT', sshport)
    return '%s:%s' % (location, sshport)


def serverLocationBasicAuth():
    return "http://"+geoserverLocation()+"/geoserver"


def serverLocationPkiAuth():
    return "https://"+geoserverLocationSsh()+"/geoserver"

#######################################################################
#     PKI config utils
#######################################################################


def initAuthManager():
    """
    Setup AuthManager instance.

    heavily based on testqgsauthmanager.cpp.
    """
    global AUTHM
    if not AUTHM:
        AUTHM = QgsAuthManager.instance()
        # check if QgsAuthManager has been already initialised... a side effect
        # of the QgsAuthManager.init() is that AuthDbPath is set
        if AUTHM.authenticationDbPath():
            # already initilised => we are inside QGIS. Assumed that the
            # actual qgis_auth.db has the same master pwd as AUTHDB_MASTERPWD
            if AUTHM.masterPasswordIsSet():
                msg = 'Auth master password have to be set to: ' + AUTHDB_MASTERPWD
                assert AUTHM.masterPasswordSame(AUTHDB_MASTERPWD), msg
            else:
                msg = 'Master password could not be set'
                assert AUTHM.setMasterPassword(AUTHDB_MASTERPWD, True), msg
        else:
            # outside qgis => setup env var before db init
            os.environ['QGIS_AUTH_DB_DIR_PATH'] = AUTHDBDIR
            msg = 'Master password could not be set'
            assert AUTHM.setMasterPassword(AUTHDB_MASTERPWD, True), msg
            AUTHM.init(AUTHDBDIR)


def populatePKITestCerts():
    """
    Populate AuthManager with test certificates.

    heavily based on testqgsauthmanager.cpp.
    """
    global AUTHM
    global AUTHCFGID
    global AUTHTYPE
    assert (AUTHM is not None)
    if AUTHCFGID:
        removePKITestCerts()
    assert (AUTHCFGID is None)
    # set alice PKI data
    p_config = QgsAuthMethodConfig()
    p_config.setName("alice")
    p_config.setMethod("PKI-Paths")
    p_config.setUri("http://example.com")
    p_config.setConfig("certpath", os.path.join(PKIDATA, 'alice-cert.pem'))
    p_config.setConfig("keypath", os.path.join(PKIDATA, 'alice-key.pem'))
    assert p_config.isValid()
    # add authorities
    cacerts = QSslCertificate.fromPath(os.path.join(PKIDATA, 'subissuer-issuer-root-ca_issuer-2-root-2-ca_chains.pem'))
    assert cacerts is not None
    AUTHM.storeCertAuthorities(cacerts)
    AUTHM.rebuildCaCertsCache()
    AUTHM.rebuildTrustedCaCertsCache()
    # add alice cert
    # boundle = QgsPkiBundle.fromPemPaths(os.path.join(PKIDATA, 'alice-cert.pem'),
    #                                    os.path.join(PKIDATA, 'alice-key_w-pass.pem'),
    #                                    'password',
    #                                    cacerts)
    # assert boundle is not None
    # assert boundle.isValid()

    # register alice data in auth
    AUTHM.storeAuthenticationConfig(p_config)
    AUTHCFGID = p_config.id()
    assert (AUTHCFGID is not None)
    assert (AUTHCFGID != '')
    AUTHTYPE = p_config.method()
    # # get client cert
    # clientcert = None
    # certpath = os.path.join(PKIDATA, 'alice-cert.pem')
    # certs = QgsAuthCertUtils.certsFromFile(certpath)
    # assert certs is not None
    # clientcert = certs
    # print certs
    #
    # # get private key
    # keypath = os.path.join(PKIDATA, 'alice-key.pem')
    # with open(keypath, 'r') as keyFile:
    #     keydata = keyFile.readAll()
    #
    # clientkey = QSslKey(keydata, QSsl.Rsa, True, QSsl.PrivateKey, None)
    # assert clientkey
    # AUTHM.storeCertIdentity(clientcert, clientkey)
    # AUTHTYPE = "PKI-Paths"
    # AUTHCFGID = QgsAuthCertUtils.shaHexForCert(clientcert)


def removePKITestCerts():
    """
    Remove test certificates from AuthManager.

    heavily based on testqgsauthmanager.cpp.
    """
    global AUTHM
    global AUTHCFGID
    assert (AUTHM is not None)
    assert (AUTHCFGID is not None)

    if AUTHCFGID:
        AUTHM.removeAuthenticationConfig(AUTHCFGID)
        AUTHCFGID = None
    AUTHM = None


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
    global AUTHM
    if AUTHM:
        # connect and prepare pki catalog
        catWrapper = getGeoServerCatalog(authcfgid=AUTHCFGID,
                                         authtype=AUTHTYPE)
    else:
        catWrapper = getGeoServerCatalog()

    return catWrapper
    # return RetryCatalog(serverLocationBasicAuth()+"/rest", "admin", "geoserver")


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
    stores = cat.get_stores("test_workspace")
    assert len(stores) != 0


def clean():
    global AUTHM
    cat = getCatalog().catalog
    ws = cat.get_workspace("test_workspace")
    if ws:
        cat.delete(ws, recurse=True)
        ws = cat.get_workspace(ws.name)
        assert ws is None


def cleanAndPki():
    clean()
    removePKITestCerts()


def openAndUpload():
    global AUTHM
    global AUTHCFGID
    loadTestData()
    layer = layerFromName("qgis_plugin_test_pt1")
    catWrapper = setUpCatalogAndWorkspace()
    cat = catWrapper.catalog
    # catWrapper = CatalogWrapper(cat)
    catWrapper.publishLayer(layer, "test_workspace", True)
    stores = cat.get_stores("test_workspace")
    assert len(stores) != 0
    quri = QgsDataSourceURI()
    quri.setParam("layers", 'test_workspace:qgis_plugin_test_pt1')
    quri.setParam("styles", 'qgis_plugin_test_pt1')
    quri.setParam("format", 'image/png')
    quri.setParam("crs", 'EPSG:4326')
    if AUTHM:
        quri.setParam("url", serverLocationPkiAuth()+'/wms')
    else:
        quri.setParam("url", serverLocationBasicAuth()+'/wms')
    # add authcfg if in PKI context
    if AUTHCFGID:
        quri.setParam("authcfg", AUTHCFGID)

    print str(quri.encodedUri())

    wmsLayer = QgsRasterLayer(str(quri.encodedUri()), "WMS", 'wms')
    assert wmsLayer.isValid()
    QgsMapLayerRegistry.instance().addMapLayer(wmsLayer)
    qgis.utils.iface.zoomToActiveLayer()


def layerFromName(name):
    '''
    Returns the layer from the current project with the passed name
    Returns None if no layer with that name is found
    If several layers with that name exist, only the first one is returned
    '''
    layers = QgsMapLayerRegistry.instance().mapLayers().values()
    for layer in layers:
        if layer.name() == name:
            return layer


class UtilsTestCase(unittest.TestCase):

    RE_ATTRIBUTES = b'[^>\s]+=[^>\s]+'

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
                self.assertEqual(re.findall(b'<([^>\s]+)[ >]', expected_line)[0],
                                 re.findall(b'<([^>\s]+)[ >]', response_line)[0], msg=msg + "\nTag mismatch on line %s: %s != %s" % (line_no, expected_line, response_line))
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
