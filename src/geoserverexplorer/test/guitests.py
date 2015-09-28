import unittest
from qgis.core import *
from PyQt4.QtCore import *
from PyQt4.QtGui import QWidget, QHBoxLayout, QToolTip
from PyQt4.QtTest import QTest
from geoserverexplorer.gui.dialogs.catalogdialog import DefineCatalogDialog
from geoserverexplorer.gui.explorer import GeoServerExplorer
from geoserverexplorer.gui.dialogs.groupdialog import LayerGroupDialog
from geoserverexplorer.test.integrationtest import ExplorerIntegrationTest
from geoserverexplorer.test.utils import *
from geoserverexplorer.gui.dialogs.layerdialog import PublishLayersDialog
from geoserver.catalog import Catalog
from geoserverexplorer.qgis import layers
from geoserverexplorer.gui.gsnameutils import GSNameWidget, xmlNameRegex, \
    xmlNameRegexMsg, xmlNameFixUp
from geoserverexplorer.gui.dialogs.gsnamedialog import GSNameDialog
from geoserverexplorer.gui.contextualhelp import InfoIcon
from geoserverexplorer.gui.gsnameutils import xmlNameEmptyRegex

class CreateCatalogDialogTests(unittest.TestCase):

    explorer = GeoServerExplorer()

    def setUp(self):
        self.cat = getGeoServerCatalog()

    def testCreateCatalogDialog(self):
        dialog = DefineCatalogDialog(self.explorer)
        dialog.nameBox.setText("name")
        dialog.urlBox.setText("http://localhost:8080/geoserver")
        dialog.passwordBox.setText("password")
        dialog.usernameBox.setText("username")
        okWidget = dialog.buttonBox.button(dialog.buttonBox.Ok)
        QTest.mouseClick(okWidget, Qt.LeftButton)
        self.assertTrue(dialog.ok)
        self.assertEquals("username", dialog.username)
        self.assertEquals("password", dialog.password)
        self.assertEquals("name", dialog.name)
        self.assertEquals("http://localhost:8080/geoserver/rest", dialog.url)
        settings = QSettings()
        settings.endGroup()
        settings.beginGroup("/GeoServer/Catalogs/name")
        settings.remove("")
        settings.endGroup()

    def testCreateCatalogDialogWithUrlWithoutProtocol(self):
        dialog = DefineCatalogDialog(self.explorer)
        dialog.nameBox.setText("name")
        dialog.urlBox.setText("localhost:8080/geoserver")
        dialog.passwordBox.setText("password")
        dialog.usernameBox.setText("username")
        okWidget = dialog.buttonBox.button(dialog.buttonBox.Ok)
        QTest.mouseClick(okWidget, Qt.LeftButton)
        self.assertTrue(dialog.ok)
        self.assertEquals("username", dialog.username)
        self.assertEquals("password", dialog.password)
        self.assertEquals("name", dialog.name)
        self.assertEquals("http://localhost:8080/geoserver/rest", dialog.url)
        settings = QSettings()
        settings.endGroup()
        settings.beginGroup("/GeoServer/Catalogs/name")
        settings.remove("")
        settings.endGroup()

    def testCreateCatalogDialogUsingExistingName(self):
        self.explorer.catalogs()["name"] = self.cat
        dialog = DefineCatalogDialog(self.explorer)
        dialog.nameBox.setText("name")
        okWidget = dialog.buttonBox.button(dialog.buttonBox.Ok)
        QTest.mouseClick(okWidget, Qt.LeftButton)
        self.assertEquals("name_2", dialog.name)
        settings = QSettings()
        settings.beginGroup("/GeoServer/Catalogs/name")
        settings.remove("")
        settings.endGroup()
        settings.beginGroup("/GeoServer/Catalogs/name_2")
        settings.remove("")
        settings.endGroup()
        del self.explorer.catalogs()["name"]

    def testLastCatalogNameIsShownByDefault(self):
        dialog = DefineCatalogDialog(self.explorer)
        dialog.nameBox.setText("catalogname")
        dialog.urlBox.setText("localhost:8081/geoserver")
        okWidget = dialog.buttonBox.button(dialog.buttonBox.Ok)
        QTest.mouseClick(okWidget, Qt.LeftButton)
        self.assertTrue(dialog.ok)
        self.assertEquals("catalogname", dialog.name)
        self.assertEquals("http://localhost:8081/geoserver/rest", dialog.url)
        dialog = DefineCatalogDialog(self.explorer)
        self.assertEquals("catalogname", dialog.nameBox.text())
        self.assertEquals("localhost:8081/geoserver", dialog.urlBox.text())
        okWidget = dialog.buttonBox.button(dialog.buttonBox.Ok)
        QTest.mouseClick(okWidget, Qt.LeftButton)
        settings = QSettings()
        settings.endGroup()
        settings.beginGroup("/GeoServer/Catalogs/catalogname")
        settings.remove("")
        settings.endGroup()

class GroupDialogTests(ExplorerIntegrationTest):

    explorer = GeoServerExplorer()

    def testGroupDialogWithEmptyName(self):
        dialog = LayerGroupDialog(self.cat)
        dialog.nameBox.setName("")
        okWidget = dialog.buttonBox.button(dialog.buttonBox.Ok)
        self.assertFalse(okWidget.isEnabled())

    def testGroupDialogWithNameContaingBlankSpaces(self):
        dialog = LayerGroupDialog(self.cat)
        dialog.nameBox.setName("my group")
        dialog.table.cellWidget(0, 0).setChecked(True)
        okWidget = dialog.buttonBox.button(dialog.buttonBox.Ok)
        self.assertFalse(okWidget.isEnabled())

    def testSelectAllButton(self):
        dialog = LayerGroupDialog(self.cat)
        QTest.mouseClick(dialog.selectAllButton, Qt.LeftButton)
        for i in range(dialog.table.rowCount()):
            self.assertTrue(dialog.table.cellWidget(i, 0).isChecked())
        QTest.mouseClick(dialog.selectAllButton, Qt.LeftButton)
        for i in range(dialog.table.rowCount()):
            self.assertFalse(dialog.table.cellWidget(i, 0).isChecked())

    def testCannotEditName(self):
        group = self.cat.get_layergroup(GROUP)
        self.assertIsNotNone(group)
        dialog = LayerGroupDialog(self.cat, group)
        self.assertFalse(dialog.nameBox.isEnabled())

class LayerDialogTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.explorer = GeoServerExplorer()
        cls.cat = Catalog("http://localhost:8080/geoserver/rest", "admin", "geoserver")
        cls.catalogs = {"catalog": cls.cat}
        cleanCatalog(cls.cat)
        cls.cat.create_workspace(WORKSPACE, "http://test1.com")
        cls.cat.create_workspace(WORKSPACEB, "http://test2.com")

    @classmethod
    def tearDownClass(cls):
        cleanCatalog(cls.cat)


    def testPublishLayersDialog(self):
        pt1 = layers.resolveLayer(PT1)
        pt2 = layers.resolveLayer(PT2)
        dialog = PublishLayersDialog(self.catalogs, [pt1,pt2])
        cancelWidget = dialog.buttonBox.button(dialog.buttonBox.Cancel)
        QTest.mouseClick(cancelWidget, Qt.LeftButton)
        self.assertIsNone(dialog.topublish)

        cat = self.catalogs.values()[0]
        for idx, ws in enumerate(cat.get_workspaces()):
            if ws.name == WORKSPACE:
                wsIdx = idx
            if ws.name == WORKSPACEB:
                wsIdxB = idx
        dialog = PublishLayersDialog(self.catalogs, [pt1,pt2])
        self.assertEquals(1, dialog.table.columnCount())
        self.assertEquals(2, dialog.table.rowCount())
        dialog.table.cellWidget(0,0).setCurrentIndex(wsIdx)
        dialog.table.cellWidget(1,0).setCurrentIndex(wsIdxB)
        okWidget = dialog.buttonBox.button(dialog.buttonBox.Ok)
        QTest.mouseClick(okWidget, Qt.LeftButton)
        self.assertIsNotNone(dialog.topublish)
        self.assertEquals(WORKSPACE, dialog.topublish[0][2].name)
        self.assertEquals(WORKSPACEB, dialog.topublish[1][2].name)

        dialog = PublishLayersDialog({"catalog": cat, "catalog2:": cat}, [pt1,pt2])
        self.assertEquals(2, dialog.table.columnCount())
        self.assertEquals(2, dialog.table.rowCount())
        dialog.table.cellWidget(0,1).setCurrentIndex(wsIdx)
        dialog.table.cellWidget(1,1).setCurrentIndex(wsIdxB)
        okWidget = dialog.buttonBox.button(dialog.buttonBox.Ok)
        QTest.mouseClick(okWidget, Qt.LeftButton)
        self.assertIsNotNone(dialog.topublish)
        self.assertEquals(WORKSPACE, dialog.topublish[0][2].name)
        self.assertEquals(WORKSPACEB, dialog.topublish[1][2].name)



class GsNameUtilsTest(unittest.TestCase):

    def testGSNameStaticUtils(self):
        n = xmlNameFixUp('My PG connection')
        self.assertTrue(n == 'My_PG_connection')
        n = xmlNameFixUp('0Name_with_number')
        self.assertTrue(n == '_0Name_with_number')
        n = xmlNameFixUp('xml_starts_name')
        self.assertTrue(n == '_xml_starts_name')
        n = xmlNameFixUp(':Name_startswith_punctuation')
        self.assertTrue(n == '_:Name_startswith_punctuation')
        nr = xmlNameRegex()
        self.assertTrue(QRegExp(nr, 0).isValid())
        nrm = xmlNameRegexMsg()
        self.assertTrue('XML name' in nrm)

    def testGSNameWidgetInit(self):
        nw = GSNameWidget(
            namemsg='Sample is generated from PostgreSQL connection name',
            name=xmlNameFixUp('My PG connection'),
            nameregex=xmlNameRegex(),
            nameregexmsg=xmlNameRegexMsg(),
            names=['name_one', 'name_two', 'name_three'],
            unique=False,
            maxlength=10)
        self.assertEqual(nw.nameBox.count(), 4)  # name is prepended to list

    def testGSNameWidgetValidName(self):
        nw = GSNameWidget(name='my_pg_connection')
        self.assertTrue(nw.isValid())
        self.assertIsNotNone(nw.definedName())
        self.assertEqual(nw.definedName(), 'my_pg_connection')

        nw.validateName('my_pg_connection')
        self.assertTrue(nw.isValid())
        nw.highlightName()
        self.assertEqual(nw.nameBox.lineEdit().styleSheet(), '')

        validnames = ['name_8291', 'name.with.dots', 'name:with::colons',
                      '_name_with_underscore']

        # XML valid name
        nw.setNameRegex(xmlNameRegex(), xmlNameRegexMsg())
        self.assertTrue(nw.isValid())
        for vname in validnames:
            nw.setName(vname)
            self.assertTrue(nw.isValid())

        # empty name regex
        nw.setName('')
        nw.setNameRegex(xmlNameEmptyRegex(), xmlNameRegexMsg())
        self.assertTrue(nw.isValid())
        nw.setAllowEmpty(True)
        self.assertTrue(nw.isValid())
        self.assertEqual(nw.definedName(), '')
        for vname in validnames:
            nw.setName(vname)
            self.assertTrue(nw.isValid())

    def testGSNameWidgetInvalidName(self):
        # base invalid name is empty
        nw = GSNameWidget(name='')
        self.assertFalse(nw.isValid())

        nw.validateName('')
        self.assertFalse(nw.isValid())
        nw.highlightName()
        self.assertNotEqual(nw.nameBox.lineEdit().styleSheet(), '')

        invalidnames = ['xMl_name', 'name with spaces', '9starts_with_number',
                        ':starts_with_punctuation']

        # XML invalid name
        nw.setNameRegex(xmlNameRegex(), xmlNameRegexMsg())
        self.assertFalse(nw.isValid())
        self.assertIsNone(nw.definedName())
        for ivname in invalidnames:
            nw.setName(ivname)
            self.assertFalse(nw.isValid())

        # empty name regex
        nw.setName('')
        nw.setNameRegex(xmlNameEmptyRegex(), xmlNameRegexMsg())
        self.assertTrue(nw.isValid())
        self.assertEqual(nw.definedName(), '')
        for ivname in invalidnames:
            nw.setName(ivname)
            self.assertFalse(nw.isValid())

        # custom regex invalid name
        nw.setNameRegex(r'^(?!XML|\d|\W)[a-z](\S(?!::))*', 'regex message')
        nw.setName('my::name')
        self.assertFalse(nw.isValid())

    def testGSNameWidgetUniqueName(self):
        nw = GSNameWidget(
            name='my_pg_connection',
            names=['name_one', 'name_two', 'name_three'],
            unique=False)
        self.assertTrue(nw.isValid())
        nw.setName('name_one')
        self.assertTrue(nw.isValid())
        self.assertTrue(nw.overwritingName())
        nw.setUnique(True)
        self.assertFalse(nw.isValid())
        self.assertFalse(nw.overwritingName())
        nw.setUnique(False)
        self.assertTrue(nw.isValid())
        self.assertTrue(nw.overwritingName())

    def testGSNameWidgetNames(self):
        nw = GSNameWidget(
            name='name_one',
            names=['name_one', 'name_two', 'name_three'],
            unique=True)
        self.assertFalse(nw.isValid())

        nw.setNames(['name_four', 'name_five'])
        self.assertTrue(nw.isValid())
        self.assertEqual(nw.nameBox.count(), 3)  # 'name_one' prepended to list
        self.assertEqual(nw.definedName(), 'name_one')
        nw.setName('name_four')
        self.assertFalse(nw.isValid())
        self.assertIsNone(nw.definedName())

        nw.setName('name')
        nw.setNames(['name_one', 'name_two', 'name_three'])
        self.assertTrue(nw.isValid())
        self.assertEqual(nw.nameBox.count(), 4)  # 'name' is prepended to list
        self.assertEqual(nw.definedName(), 'name')

        nw.setNames([])
        self.assertTrue(nw.isValid())
        self.assertEqual(nw.nameBox.count(), 1)  # 'name' is prepended to list
        self.assertEqual(nw.definedName(), 'name')

    def testGSNameWidgetMaxLenName(self):
        nw = GSNameWidget(
            name='my_pg_connection',
            maxlength=10)
        self.assertFalse(nw.isValid())
        nw.setName('my_pg_conn')
        self.assertTrue(nw.isValid())
        nw.setMaxLength(5)
        self.assertFalse(nw.isValid())
        nw.setMaxLength(10)
        self.assertTrue(nw.isValid())


class GSNameDialogTest(unittest.TestCase):

    def testGSNameDialog(self):
        ndlg = GSNameDialog(
            boxtitle='GeoServer data store name',
            boxmsg='My groupbox message',
            namemsg='Sample is generated from PostgreSQL connection name.',
            name=xmlNameFixUp('My PG connection'),
            nameregex=xmlNameRegex(),
            nameregexmsg=xmlNameRegexMsg(),
            names=['name_one', 'name_two', 'name_three'],
            unique=True,
            maxlength=10)

        # maxlength > 10
        self.assertFalse(ndlg.okButton.isEnabled())
        self.assertIsNone(ndlg.definedName())
        self.assertFalse(ndlg.overwritingName())

        # maxlength = 10
        ndlg.nameBox.setName('my_pg_conn')
        self.assertTrue(ndlg.okButton.isEnabled())
        self.assertEqual(ndlg.definedName(), 'my_pg_conn')
        self.assertFalse(ndlg.overwritingName())

        # unique = True
        ndlg.nameBox.setName('name_one')
        self.assertIsNone(ndlg.definedName())
        self.assertFalse(ndlg.okButton.isEnabled())
        self.assertFalse(ndlg.overwritingName())

        del ndlg
        # unique=False
        ndlg = GSNameDialog(
            boxtitle='GeoServer data store name',
            boxmsg='My groupbox message',
            name='name',
            names=['name_one', 'name_two', 'name_three'],
            unique=False)

        # not overwriting
        self.assertEqual(ndlg.definedName(), 'name')
        self.assertTrue(ndlg.okButton.isEnabled())
        self.assertFalse(ndlg.overwritingName())
        # overwriting
        ndlg.nameBox.setName('name_one')
        self.assertEqual(ndlg.definedName(), 'name_one')
        self.assertTrue(ndlg.okButton.isEnabled())
        self.assertTrue(ndlg.overwritingName())




def suite():
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(CreateCatalogDialogTests, 'test'))
    suite.addTests(unittest.makeSuite(GroupDialogTests, 'test'))
    suite.addTests(unittest.makeSuite(LayerDialogTests, 'test'))
    return suite
