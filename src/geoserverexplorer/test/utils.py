import os
from geoserver.util import shapefile_and_friends
from geoserverexplorer.qgis.catalog import createGeoServerCatalog

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
GSHOSTNAME = 'localhost'
GSPORT = '8080'
GSSSHPORT = '8443' 
GSUSER = 'admin'
GSPASSWORD = 'geoserver'

# pki envs
AUTHDB_MASTERPWD = 'pass'
AUTHCFGID = 'y45c26z' # Fra user has id y45c26z in the test qgis_auth.db
AUTHTYPE = 'Identity-Cert' # other are "PKI-Paths" and 'PKI-PKCS#12'

# authdb and cert data
AUTH_TESTDATA = os.path.join(os.path.dirname(__file__), "resources", 'auth_system')
#PKIDATA = os.path.join(AUTH_TESTDATA, 'certs_keys')
#AUTHDBDIR = tempfile.mkdtemp()

def getGeoServerCatalog(authcfgid=None, authtype=None):
    # beaware that these envs can be overrided by os.environ envs cnaging
    # the function behaviour
    if authcfgid:
        conf = dict(
            URL = serverLocationPkiAuth()+'/rest',
            USER = None,
            PASSWORD = None,
            AUTHCFG = authcfgid,
            AUTHTYPE = authtype
        )
    else:
        conf = dict(
            URL = serverLocationBasicAuth()+'/rest',
            USER = GSUSER,
            PASSWORD = GSPASSWORD,
            AUTHCFG = authcfgid,
            AUTHTYPE = authtype
        )
    conf.update([ (k,os.getenv('GS%s' % k)) for k in conf if 'GS%s' % k in os.environ])
    cat = createGeoServerCatalog(conf['URL'], conf['USER'], conf['PASSWORD'], conf['AUTHCFG'], conf['AUTHTYPE'])
    try:
        cat.catalog.gsversion()
    except Exception, ex:
        msg = 'cannot reach geoserver using provided credentials %s, msg is %s'
        raise AssertionError(msg % (conf,ex))
    return cat


def cleanCatalog(cat):

    for groupName in [GROUP, GEOLOGY_GROUP]:
        group = cat.get_layergroup(groupName)
        if group is not None:
            cat.delete(group)
            group = cat.get_layergroup(groupName)
            assert group is None

    toDelete = []
    for layer in cat.get_layers():
        if layer.name.startswith(PREFIX):
            toDelete.append(layer)
    for style in cat.get_styles():
        if style.name.startswith(PREFIX):
            toDelete.append(style)

    for e in toDelete:
        cat.delete(e, purge = True)

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
    sldfile = os.path.join(os.path.dirname(__file__), "resources", "vector.sld")
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

