# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
import os
from collections import defaultdict
from qgis.core import *
from qgis.gui import *
from PyQt4 import QtGui,QtCore
from geoserverexplorer.qgis import layers as qgislayers
from geoserver.store import DataStore
from geoserver.resource import Coverage, FeatureType
from dialogs.catalogdialog import DefineCatalogDialog
from geoserver.style import Style
from geoserver.layer import Layer
from dialogs.styledialog import AddStyleToLayerDialog, StyleFromLayerDialog
from geoserverexplorer.qgis.catalog import CatalogWrapper
from geoserverexplorer.gui.exploreritems import TreeItem
from dialogs.groupdialog import LayerGroupDialog
from dialogs.workspacedialog import DefineWorkspaceDialog
from geoserver.layergroup import UnsavedLayerGroup
from geoserver.catalog import FailedRequestError
import traceback
from geoserverexplorer.geoserver.wps import Wps
from dialogs.crsdialog import CrsSelectionDialog
from geoserverexplorer.geoserver.settings import Settings
from geoserverexplorer.gui.parametereditor import ParameterEditor
from dialogs.sldeditor import SldEditorDialog
from geoserverexplorer.gui.gwcexploreritems import GwcLayersItem
from geoserverexplorer import config
from geoserverexplorer.qgis.utils import *
from geoserverexplorer.qgis.sldadapter import adaptGsToQgs, getGeomTypeFromSld,\
    getGsCompatibleSld
from geoserverexplorer.gui.confirm import *
from geoserverexplorer.geoserver.util import getLayerFromStyle
from geoserverexplorer.gui.confirm import confirmDelete
from geoserverexplorer.geoserver.pki import PKICatalog
from _ssl import SSLError
from geoserverexplorer.geoserver import pem
from geoserverexplorer.gui.gsoperations import *
from geoserverexplorer.geoserver.retry import RetryCatalog
from geoserverexplorer.gui.gsoperations import addDraggedStyleToLayer

class GsTreeItem(TreeItem):

    def parentCatalog(self):
        if hasattr(self, 'catalog') and self.catalog is not None:
            return self.catalog
        item  = self
        while item is not None:
            if isinstance(item, GsCatalogItem):
                return item.element
            if hasattr(item, 'catalog') and item.catalog is not None:
                return item.catalog
            item = item.parent()
        return None

    def refreshParentCatalog(self):
        item  = self
        while item is not None:
            if isinstance(item, GsCatalogItem):
                item.refreshContent()
                return
            if hasattr(item, 'catalog') and item.catalog is not None:
                item.refreshContent()
                return
            item = item.parent()

    def parentWorkspace(self):
        item  = self
        while item is not None:
            if isinstance(item, GsWorkspaceItem):
                return item.element
            item = item.parent()
        return None

    def getDefaultWorkspace(self):
        workspaces = self.parentCatalog().get_workspaces()
        if workspaces:
            return self.parentCatalog().get_default_workspace()
        else:
            return None

    def deleteElements(self, selected, tree, explorer):
        elements = []
        uniqueStyles = []
        workspacesToUpdate = []
        for item in selected:
            elements.append(item.element)
            if isinstance(item, GsStoreItem):
                for idx in range(item.childCount()):
                    subitem = item.child(idx)
                    elements.insert(0, subitem.element)
            elif isinstance(item, GsLayerItem):
                uniqueStyles.extend(self.uniqueStyles(item.element))
                workspace = item.element.resource.workspace
                workspacesToUpdate.extend(tree.findAllItems(workspace))
            elif isinstance(item, GsWorkspaceItem):
                for idx in range(item.childCount()):
                    subitem = item.child(idx)
                    for subidx in range(subitem.childCount()):
                        subsubitem = subitem.child(subidx)
                        elements.insert(0, subsubitem.element)
        toUpdate = set(item.parent() for item in selected)
        progress = 0
        dependent = self.getDependentElements(elements, tree)
        if dependent:
            depdlg = DeleteDependentsDialog(dependent)
            if not depdlg.exec_():
                return
            toDelete = set()
            for e in dependent:
                items = tree.findAllItems(e);
                toUpdate.update(set(item.parent() for item in items))
                toDelete.update(items)
            toUpdate = toUpdate - toDelete
        elif not confirmDelete():
            return
        settings = QtCore.QSettings()
        deleteStyle = bool(settings.value("/GeoServer/Settings/GeoServer/DeleteStyle", True, bool))
        recurse = bool(settings.value("/GeoServer/Settings/GeoServer/Recurse", True, bool))

        elements[0:0] = dependent
        if recurse:
            toUpdate.update(workspacesToUpdate)
        if deleteStyle:
            elements.extend(uniqueStyles)
            stylesEntriesToUpdate = set()
            for e in uniqueStyles:
                items = tree.findAllItems(e);
                for item in items:
                    #the item representing the layer we are deleting will be here, but we have to ignore it
                    #and update only the "styles" item
                    if isinstance(item.parent(), GsStylesItem):
                        stylesEntriesToUpdate.add(item.parent())
                        break
            toUpdate.update(stylesEntriesToUpdate)
        explorer.setProgressMaximum(len(elements), "Deleting elements")
        for progress, element in enumerate(elements):
            explorer.setProgress(progress)
            #we run this delete operation this way, to ignore the error in case we are trying to delete
            #something that doesn't exist which might happen if a previous deletion has purged the element
            #we now want to delete. It is deleted already anyway, so we should not raise any exception
            #TODO: this might swallow other type of exceptions. Should implement a more fine-grained error handling
            try:
                if isinstance(element, Style):
                    layersToUpdate = []
                    layers = element.catalog.get_layers()
                    for layer in layers:
                        styles = layer.styles
                        if not styles:
                            continue
                        if layer.default_style.name == element.name:
                            layersToUpdate.append(layer)
                        else:
                            for style in styles:
                                if style.name == element.name:
                                    layersToUpdate.append(layer)
                                    break
                    for layer in layersToUpdate:
                        styles = layer.styles
                        styles = [style for style in styles if style.name != element.name]
                        layer.styles = styles
                        element.catalog.save(layer)
                        toUpdate.add(tree.findAllItems(layer)[0])
                element.catalog.delete(element, recurse = recurse, purge = True)
            except:
                pass
        explorer.setProgress(len(elements))
        for item in toUpdate:
            if item is not None:
                item.refreshContent(explorer)
        if None in toUpdate:
            explorer.refreshContent()
        explorer.resetActivity()
        explorer.setDescriptionWidget()
        explorer.setToolbarActions([])

    def uniqueStyles(self, layer):
        '''returns the styles used by a layer that are not used by any other layer'''
        unique = []
        allUsedStyles = set()
        catalog = layer.catalog
        layers = catalog.get_layers()
        for lyr in layers:
            if lyr.name == layer.name:
                continue
            for style in lyr.styles:
                allUsedStyles.add(style.name)
                if lyr.default_style is not None:
                    allUsedStyles.add(lyr.default_style.name)
        for style in layer.styles:
            if style.name not in allUsedStyles:
                unique.append(style)
        if layer.default_style is not None and layer.default_style not in allUsedStyles:
            unique.append(layer.default_style)
        return unique

    def getDependentElements(self, elements, tree):
        dependent = []
        for element in elements:
            if isinstance(element, Layer):
                groups = element.catalog.get_layergroups()
                for group in groups:
                    if group.layers is None:
                        continue
                    for layer in group.layers:
                        if layer == element.name:
                            dependent.append(group)
                            break
                catItem = tree.findAllItems(element.catalog)[0];
                gwcItem = catItem.gwcItem
                possibleGwcLayers = []
                for idx in xrange(gwcItem.childCount()):
                    gwcLayerItem = gwcItem.child(idx)
                    gwcLayer = gwcLayerItem.element
                    if gwcLayer.name.split(":")[-1] == element.name:
                        possibleGwcLayers.append(gwcLayer)
                if len(possibleGwcLayers) == 1:
                    #Since layers have no workspace, we cannot fully compare with gwc layer names.
                    #We only delete if we are sure that the gwc layer is the only one with that name,
                    #not considering namespaces
                    dependent.append(possibleGwcLayers[0])
            elif isinstance(element, (FeatureType, Coverage)):
                layers = element.catalog.get_layers()
                for layer in layers:
                    if layer.resource.name == element.name:
                        dependent.append(layer)
            elif isinstance(element, Style):
                layers = element.catalog.get_layers()
                for layer in layers:
                    styles = layer.styles
                    if styles:
                        continue
                    if layer.default_style is not None and layer.default_style.name == element.name:
                        dependent.append(layer)
                    else:
                        for style in styles:
                            if style.name == element.name:
                                dependent.append(layer)
                                break

        if dependent:
            subdependent = self.getDependentElements(dependent, tree)
            if subdependent:
                dependent[0:0] = subdependent
        return dependent

    def iconPath(self):
        return os.path.dirname(__file__) + "/../images/geoserver.png"


class GsCatalogsItem(GsTreeItem):
    def __init__(self):
        self._catalogs = {}
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/geoserver.png")
        GsTreeItem.__init__(self, None, icon, "Catalogs")
        settings = QtCore.QSettings()
        saveCatalogs = bool(settings.value("/GeoServer/Settings/GeoServer/SaveCatalogs", True, bool))
        if saveCatalogs:
            settings.beginGroup("/GeoServer/Catalogs")
            for name in settings.childGroups():
                geoserverItem = GsCatalogItem(None, name)
                self.addChild(geoserverItem)
                settings.endGroup()
            settings.endGroup()


    def contextMenuActions(self, tree, explorer):
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/add.png")
        createCatalogAction = QtGui.QAction(icon, "New catalog...", explorer)
        createCatalogAction.triggered.connect(lambda: self.addGeoServerCatalog(explorer))
        return [createCatalogAction]

    def addGeoServerCatalog(self, explorer):
        dlg = DefineCatalogDialog(self._catalogs)
        dlg.exec_()
        if dlg.ok:
            try:
                QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
                if dlg.certfile is not None:
                    cat = PKICatalog(dlg.url, dlg.keyfile, dlg.certfile, dlg.cafile)
                else:
                    cat = RetryCatalog(dlg.url, dlg.username, dlg.password)
                cat.authid = dlg.authid
                v = cat.gsversion()
                try:
                    supported = float(v[:3]) > 2.299
                except:
                    supported = False
                if not supported:
                    QtGui.QApplication.restoreOverrideCursor()
                    ret = QtGui.QMessageBox.warning(explorer, "GeoServer catalog definition",
                                    "The specified catalog seems to be running an older\n"
                                    "or unidentified version of GeoServer.\n"
                                    "That might cause unexpected behaviour.\nDo you want to add the catalog anyway?",
                                    QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                    QtGui.QMessageBox.No);
                    if ret == QtGui.QMessageBox.No:
                        return
                    QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
                geoserverItem = GsCatalogItem(cat, dlg.name)
                self.addChild(geoserverItem)
                geoserverItem.populate()
                self.setExpanded(True)
            except FailedRequestError, e:
                explorer.setWarning(e.args[0])
            except SSLError:
                explorer.setWarning("Cannot connect using the provided certificate/key values")
            except:
                explorer.setError("Could not connect to catalog:\n" + traceback.format_exc())
            finally:
                QtGui.QApplication.restoreOverrideCursor()

    def refreshContent(self, explorer):
        for i in xrange(self.childCount()):
            catItem = self.child(i)
            if catItem.isConnected:
                catItem.refreshContent(explorer)

class GsLayersItem(GsTreeItem):
    def __init__(self, catalog):
        self.catalog = catalog
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/layer.png")
        GsTreeItem.__init__(self, None, icon, "Layers")
        self.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDropEnabled)

    def populate(self):
        layers = self.catalog.get_layers()
        items = {}
        for layer in layers:
            if layer.name in items:
                items[layer.name].markAsDuplicated()
            else:
                layerItem = GsLayerItem(layer)
                layerItem.populate()
                self.addChild(layerItem)
                items[layer.name] = layerItem
        self.sortChildren(0, QtCore.Qt.AscendingOrder)


    def acceptDroppedUris(self, tree, explorer, uris):
        return addDraggedUrisToWorkspace(uris, self.parentCatalog(), self.getDefaultWorkspace(), explorer, tree)

class GsGroupsItem(GsTreeItem):
    def __init__(self, catalog):
        self.catalog = catalog
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/group.gif")
        GsTreeItem.__init__(self, None, icon, "Groups")

    def populate(self):
        groups = self.catalog.get_layergroups()
        for group in groups:
            groupItem = GsGroupItem(group)
            groupItem.populate()
            self.addChild(groupItem)

    def contextMenuActions(self, tree, explorer):
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/add.png")
        createGroupAction = QtGui.QAction(icon, "New group...", explorer)
        createGroupAction.triggered.connect(lambda: self.createGroup(explorer))
        return [createGroupAction]

    def createGroup(self, explorer):
        dlg = LayerGroupDialog(self.parentCatalog())
        dlg.exec_()
        group = dlg.group
        if group is not None:
            explorer.run(self.parentCatalog().save,
                     "Create group '" + group.name + "'",
                     [self],
                     group)


class GsWorkspacesItem(GsTreeItem):
    def __init__(self, catalog):
        self.catalog = catalog
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/workspace.png")
        GsTreeItem.__init__(self, None, icon, "Workspaces")
        self.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDropEnabled)

    def populate(self):
        cat = self.parentCatalog()
        try:
            defaultWorkspace = cat.get_default_workspace()
            defaultWorkspace.fetch()
            defaultName = defaultWorkspace.dom.find('name').text
        except:
            defaultName = None
        workspaces = cat.get_workspaces()
        for workspace in workspaces:
            workspaceItem = GsWorkspaceItem(workspace, workspace.name == defaultName)
            workspaceItem.populate()
            self.addChild(workspaceItem)

    def acceptDroppedUris(self, tree, explorer, uris):
        return addDraggedUrisToWorkspace(uris, self.parentCatalog(), self.getDefaultWorkspace(), explorer, tree)

    def contextMenuActions(self, tree, explorer):
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/add.png")
        createWorkspaceAction = QtGui.QAction(icon, "New workspace...", explorer)
        createWorkspaceAction.triggered.connect(lambda: self.createWorkspace(explorer))
        return [createWorkspaceAction]

    def createWorkspace(self, explorer):
        workspaces = [ws.name for ws in self.parentCatalog().get_workspaces()]
        dlg = DefineWorkspaceDialog(workspaces=workspaces)
        dlg.exec_()
        if dlg.name is not None:
            explorer.run(self.parentCatalog().create_workspace,
                    "Create workspace '" + dlg.name + "'",
                    [self],
                    dlg.name, dlg.uri)

class GsStylesItem(GsTreeItem):
    def __init__(self, catalog):
        self.catalog = catalog
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/style.png")
        GsTreeItem.__init__(self, None, icon, "Styles")
        self.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDropEnabled)

    def populate(self):
        styles = self.parentCatalog().get_styles()
        for style in styles:
            styleItem = GsStyleItem(style, False)
            self.addChild(styleItem)


    def contextMenuActions(self, tree, explorer):
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/add.png")
        createStyleFromLayerAction = QtGui.QAction(icon, "New style from QGIS layer...", explorer)
        createStyleFromLayerAction.triggered.connect(lambda: self.createStyleFromLayer(explorer))
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/clean.png")
        cleanAction = QtGui.QAction(icon, "Clean (remove unused styles)", explorer)
        cleanAction.triggered.connect(lambda: self.cleanStyles(explorer))
        consolidateStylesAction = QtGui.QAction(icon, "Consolidate styles", explorer)
        consolidateStylesAction.triggered.connect(lambda: self.consolidateStyles(tree, explorer))
        return [createStyleFromLayerAction, cleanAction, consolidateStylesAction]

    def consolidateStyles(self, tree, explorer):
        catalog = self.parentCatalog()
        catalogItem = tree.findAllItems(catalog)[0]
        cat = CatalogWrapper(self.catalog)
        explorer.run(cat.consolidateStyles, "Consolidate styles", [self, catalogItem.layersItem])

    def cleanStyles(self, explorer):
        cat = CatalogWrapper(self.catalog)
        explorer.run(cat.cleanUnusedStyles, "Clean (remove unused styles)", [self])

    def createStyleFromLayer(self, explorer):
        if checkLayers():
            catalog = self.parentCatalog()
            styles = [style.name for style in catalog.get_styles()]
            dlg = StyleFromLayerDialog(styles=styles)
            dlg.exec_()
            if dlg.layer is not None:
                cat = CatalogWrapper(self.catalog)
                explorer.run(cat.publishStyle,
                         "Create style from layer '" + dlg.layer + "'",
                         [self],
                         dlg.layer, True, dlg.name)
                self.refreshContent(explorer)


class GsCatalogItem(GsTreeItem):
    def __init__(self, catalog, name):
        self.catalog = catalog
        self.name = name
        self.isConnected = False
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/geoserver_gray.png")
        GsTreeItem.__init__(self, catalog, icon, name)
        self.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDropEnabled)

    def populate(self):
        catalogIsNone = self.catalog is None
        if catalogIsNone:
            settings = QtCore.QSettings()
            settings.beginGroup("/GeoServer/Catalogs")
            settings.beginGroup(self.name)
            url = unicode(settings.value("url"))
            username = settings.value("username")
            authid = settings.value("authid")
            QtGui.QApplication.restoreOverrideCursor()
            if authid is not None:
                if QGis.QGIS_VERSION_INT < 21200:
                    authtype = QgsAuthManager.instance().configProviderType(authid)
                    if authtype == QgsAuthType.None or authtype == QgsAuthType.Unknown:
                        raise Exception("Cannot restore catalog. Invalid or missing auth information")
                    if authtype == QgsAuthType.Basic:
                        amconfig = QgsAuthConfigBasic()
                        QgsAuthManager.instance().loadAuthenticationConfig(authid, amconfig, True)
                        password = amconfig.password()
                        username = amconfig.username()
                        self.catalog = RetryCatalog(url, username, password)
                    elif authtype in pem.nonBasicAuthTypes():
                        certfile, keyfile, cafile = pem.getPemPkiPaths(authid, authtype)
                        self.catalog = PKICatalog(url, keyfile, certfile, cafile)
                    else:
                        raise Exception("The selected authentication type is not supported")
                else:
                    authtype = QgsAuthManager.instance().configAuthMethodKey(authid)
                    if not authtype or authtype == '':
                        raise Exception("Cannot restore catalog. Invalid or missing auth information")
                    if authtype == 'Basic':
                        amconfig = QgsAuthMethodConfig()
                        QgsAuthManager.instance().loadAuthenticationConfig(authid, amconfig, True)
                        password = amconfig.config('username')
                        username = amconfig.config('password')
                        self.catalog = RetryCatalog(url, username, password)
                    elif authtype in pem.nonBasicAuthTypes():
                        certfile, keyfile, cafile = pem.getPemPkiPaths(authid, authtype)
                        self.catalog = PKICatalog(url, keyfile, certfile, cafile)
                    else:
                        raise Exception("The selected authentication type is not supported")
            else:
                password, ok = QtGui.QInputDialog.getText(None, "Catalog connection",
                                          "Enter catalog password (user:%s)" % username ,
                                          QtGui.QLineEdit.Password)
                if not ok:
                    raise UserCanceledOperation()
                self.catalog = RetryCatalog(url, username, password)
            self.catalog.authid = authid
            QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        try:
            dlg = QtGui.QProgressDialog("Retrieving catalog information", None, 0, 0  , config.iface.mainWindow())
            dlg.setWindowModality(QtCore.Qt.WindowModal);
            dlg.setMinimumDuration(1000)
            dlg.setMaximum(100)
            dlg.setValue(0)
            dlg.setMaximum(0)
            dlg.setCancelButton(None)
            #dlg.showNormal()
            QtGui.QApplication.processEvents()
            self._populate()
        except Exception, e:
            if catalogIsNone:
                self.catalog = None
            raise e
        finally:
            self.element = self.catalog
            dlg.reset()

    def _populate(self):
        self.isConnected = False
        self.workspacesItem = GsWorkspacesItem(self.catalog)
        self.workspacesItem.populate()
        self.addChild(self.workspacesItem)
        self.layersItem = GsLayersItem(self.catalog)
        self.addChild(self.layersItem)
        self.layersItem.populate()
        self.groupsItem = GsGroupsItem(self.catalog)
        self.addChild(self.groupsItem)
        self.groupsItem.populate()
        self.stylesItem = GsStylesItem(self.catalog)
        self.addChild(self.stylesItem)
        self.stylesItem.populate()
        self.gwcItem = GwcLayersItem(self.catalog)
        self.addChild(self.gwcItem)
        self.gwcItem.populate()
        self.wpsItem = GsProcessesItem(self.catalog)
        self.addChild(self.wpsItem)
        self.wpsItem.populate()
        self.settingsItem = GsSettingsItem(self.catalog)
        self.addChild(self.settingsItem)
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/geoserver.png")
        self.setIcon(0, icon)
        self.isConnected = True
        self.parent()._catalogs[self.text(0)] = self.catalog

    def _publishLayers(self, tree, explorer):
        if checkLayers() and self.checkWorkspaces():
            publishLayers(tree, explorer, self.element)

    def _publishProject(self, tree, explorer):
        if checkLayers() and self.checkWorkspaces():
            publishProject(tree, explorer, self.element)

    def checkWorkspaces(self):
        ws = self.getDefaultWorkspace()
        if ws is None:
            QtGui.QMessageBox.warning(config.iface.mainWindow(), 'No workspaces',
            "You must have at least one workspace in your catalog\n"
            "to perform this operation.",
            QtGui.QMessageBox.Ok)
            return False
        return True

    def contextMenuActions(self, tree, explorer):
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/delete.gif")
        removeCatalogAction = QtGui.QAction(icon, "Remove", explorer)
        removeCatalogAction.triggered.connect(lambda: self.removeCatalog(tree, explorer))
        actions = [removeCatalogAction]
        if self.isConnected:
            icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/clean.png")
            cleanAction = QtGui.QAction(icon, "Clean (remove unused elements)", explorer)
            cleanAction.triggered.connect(lambda: self.cleanCatalog(explorer))
            actions.append(cleanAction)
            icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/publish-to-geoserver.png")
            publishLayerAction = QtGui.QAction(icon, "Publish layers to this catalog", explorer)
            publishLayerAction.triggered.connect(lambda: self._publishLayers(tree, explorer))
            actions.append(publishLayerAction)
            publishProjectAction = QtGui.QAction(icon, "Publish QGIS project to this catalog", explorer)
            publishProjectAction.triggered.connect(lambda: self._publishProject(tree, explorer))
            actions.append(publishProjectAction)

        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/edit.png")
        editAction = QtGui.QAction(icon, "Edit...", explorer)
        editAction.triggered.connect(lambda: self.editCatalog(explorer))
        actions.append(editAction)

        return actions

    def editCatalog(self, explorer):
        dlg = DefineCatalogDialog(explorer.catalogs(), None, self.element, self.name)
        dlg.exec_()
        if dlg.ok:
            if dlg.certfile is not None:
                self.catalog = PKICatalog(dlg.url, dlg.keyfile, dlg.certfile, dlg.cafile)
            else:
                self.catalog = RetryCatalog(dlg.url, dlg.username, dlg.password)
            self.catalog.authid = dlg.authid
            if self.name != dlg.name:
                if self.name in explorer.catalogs():
                    del explorer.catalogs()[self.name]
                settings = QSettings()
                settings.beginGroup("/OpenGeo/GeoServer/" + self.name)
                settings.remove("")
                settings.endGroup()
                self.isConnected = False
                self.name = dlg.name
                self.setText(0, self.name)
                self._text = self.name

            self.setIcon(0, QtGui.QIcon(os.path.dirname(__file__) + "/../images/geoserver_gray.png"))
            self.refreshContent(explorer)


    def cleanCatalog(self, explorer):
        cat = CatalogWrapper(self.catalog)
        explorer.run(cat.clean, "Clean (remove unused element)", [self.workspacesItem, self.stylesItem])

    def removeCatalog(self, tree, explorer):
        name = self.text(0)
        if name in self.parent()._catalogs:
            del self.parent()._catalogs[name]
        settings = QtCore.QSettings()
        settings.beginGroup("/GeoServer/Catalogs/" + name)
        settings.remove("");
        settings.endGroup();
        parent = self.parent()
        parent.takeChild(self.parent().indexOfChild(self))
        tree.setItemSelected(parent, True)
        tree.treeItemClicked(parent, 0)


    def _getDescriptionHtml(self, tree, explorer):
        if self.isConnected:
            try:
                return self.catalog.about()
            except:
                return "<p><b>Could not get information from server. Try refreshing the item to update this description panel</b></p>"
        else:
            return ('<p>You are not connected to this catalog. '
                    '<a href="refresh">Refresh</a> to connect to it and populate the catalog item</p>')

    def linkClicked(self, tree, explorer, url):
        if not self.isConnected:
            if explorer.run(self.populate, "Populate GeoServer item", []):
                self.parent()._catalogs[self.text(0)] = self.catalog

    def acceptDroppedUris(self, tree, explorer, uris):
        if not self.isConnected:
            return []
        ws = self.getDefaultWorkspace()
        if ws is None:
            return []
        return addDraggedUrisToWorkspace(uris, self.element, ws, explorer, tree)


class GsLayerItem(GsTreeItem):
    def __init__(self, layer):
        self.catalog = layer.catalog
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/layer.png")
        GsTreeItem.__init__(self, layer, icon, layer.resource.title)
        self.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
                      | QtCore.Qt.ItemIsDropEnabled | QtCore.Qt.ItemIsDragEnabled)
        self.isDuplicated = False

    def populate(self):
        layer = self.element
        for style in layer.styles:
            styleItem = GsStyleItem(style, False)
            self.addChild(styleItem)
        if layer.default_style is not None:
            styleItem = GsStyleItem(layer.default_style, True)
            self.addChild(styleItem)

    def markAsDuplicated(self):
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/warning.png")
        self.setIcon(0, icon)
        self.isDuplicated = True

    def acceptDroppedItem(self, tree, explorer, item):
        if isinstance(item, GsStyleItem):
            addDraggedStyleToLayer(tree, explorer, item, self)
            return [self]
        elif isinstance(item, GsLayerItem):
            destinationItem = self.parent()
            toUpdate = []
            if isinstance(destinationItem, GsGroupItem):
                addDraggedLayerToGroup(explorer, item.element, destinationItem)
                toUpdate.append(destinationItem)
            return toUpdate
        else:
            return []


    def _getDescriptionHtml(self, tree, explorer):
        html = ""
        items = tree.selectedItems()
        # don't show if multiple items selected, but not the current item
        if not items or self in items or len(items) == 1:
            try:
                wsname = self.element.resource.workspace.name
                if self.isDuplicated:
                    iconPath = os.path.dirname(__file__) + "/../images/warning.png"
                    html += ('<p><img src="' + iconPath + '"/> &nbsp; There are several layers with this name in the catalog. '
                        + 'This results in an ambiguous situation and unfortunately we cannot differentiate between them. Only one layer is displayed.'
                        + 'This element represents the layer based on a datastore from the ' + wsname + ' workspace </p>')
                html += '<p><h3><b>Properties</b></h3></p><ul>'
                html += '<li><b>Name: </b>' + unicode(self.element.name) + '</li>\n'
                html += '<li><b>Title: </b>' + unicode(self.element.resource.title) + ' &nbsp;<a href="modify:title">Modify</a></li>\n'
                html += '<li><b>Abstract: </b>' + unicode(self.element.resource.abstract) + ' &nbsp;<a href="modify:abstract">Modify</a></li>\n'
                html += ('<li><b>SRS: </b>' + str(self.element.resource.projection) + ' &nbsp;<a href="modify:srs">Modify</a></li>\n')
                html += ('<li><b>Datastore workspace: </b>' + wsname + ' </li>\n')
                bbox = self.element.resource.latlon_bbox
                if bbox is not None:
                    html += '<li><b>Bounding box (lat/lon): </b></li>\n<ul>'
                    html += '<li> N:' + str(bbox[3]) + '</li>'
                    html += '<li> S:' + str(bbox[2]) + '</li>'
                    html += '<li> E:' + str(bbox[0]) + '</li>'
                    html += '<li> W:' + str(bbox[1]) + '</li>'
                    html += '</ul>'
                html += '</ul>'
            except:
                html = "<p><b>Could not get layer information from server. Try refreshing the layer to update this description panel</b></p>"

        actions = self.contextMenuActions(tree, explorer)
        items = tree.selectedItems()
        if len(items) > 1:
            actions = self.multipleSelectionContextMenuActions(
                tree, explorer, items)
        actsenabled = [act for act in actions if act.isEnabled()]
        if actsenabled:
            html += "<p><h3><b>Available actions</b></h3></p><ul>"
            for action in actsenabled:
                html += '<li><a href="' + action.text() + '">' + action.text() + '</a></li>\n'
            html += '</ul>'
        return html

    def linkClicked(self, tree, explorer, url):
        actionName = url.toString()
        if actionName == 'modify:title':
            text, ok = QtGui.QInputDialog.getText(None, "New title", "Enter new title", text=self.element.resource.title)
            if ok:
                r = self.element.resource
                r.title = text
                explorer.run(self.catalog.save, "Update layer title", [], r)
        elif actionName == 'modify:abstract':
            text, ok = QtGui.QInputDialog.getText(None, "New abstract", "Enter new abstract", text=self.element.resource.abstract)
            if ok:
                r = self.element.resource
                r.abstract = text
                explorer.run(self.catalog.save, "Update layer abstract", [], r)
        elif actionName == 'modify:srs':
            dlg = CrsSelectionDialog()
            dlg.exec_()
            if dlg.authid is not None:
                r = self.element.resource
                r.dirty['srs'] = str(dlg.authid)
                explorer.run(self.catalog.save, "Update layer srs", [], r)
        else:
            TreeItem.linkClicked(self, tree, explorer, url)

    def contextMenuActions(self, tree, explorer):
        actions = []
        if isinstance(self.parent(), GsGroupItem):
            layers = self.parent().element.layers
            count = len(layers)
            idx = layers.index(self.element.name)
            icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/delete.gif")
            removeLayerFromGroupAction = QtGui.QAction(icon, "Remove layer from group", explorer)
            removeLayerFromGroupAction.setEnabled(count > 1)
            removeLayerFromGroupAction.triggered.connect(lambda: self.removeLayerFromGroup(explorer))
            actions.append(removeLayerFromGroupAction)
            icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/up.png")
            moveLayerUpInGroupAction = QtGui.QAction(icon, "Move up", explorer)
            moveLayerUpInGroupAction.setEnabled(count > 1 and idx > 0)
            moveLayerUpInGroupAction.triggered.connect(lambda: self.moveLayerUpInGroup(explorer))
            actions.append(moveLayerUpInGroupAction)
            icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/down.png")
            moveLayerDownInGroupAction = QtGui.QAction(icon, "Move down", explorer)
            moveLayerDownInGroupAction.setEnabled(count > 1 and idx < count - 1)
            moveLayerDownInGroupAction.triggered.connect(lambda: self.moveLayerDownInGroup(explorer))
            actions.append(moveLayerDownInGroupAction)
            icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/top.png")
            moveLayerToFrontInGroupAction = QtGui.QAction(icon, "Move to front", explorer)
            moveLayerToFrontInGroupAction.setEnabled(count > 1 and idx > 0)
            moveLayerToFrontInGroupAction.triggered.connect(lambda: self.moveLayerToFrontInGroup(explorer))
            actions.append(moveLayerToFrontInGroupAction)
            icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/bottom.png")
            moveLayerToBackInGroupAction = QtGui.QAction(icon, "Move to back", explorer)
            moveLayerToBackInGroupAction.setEnabled(count > 1 and idx < count - 1)
            moveLayerToBackInGroupAction.triggered.connect(lambda: self.moveLayerToBackInGroup(explorer))
            actions.append(moveLayerToBackInGroupAction)
        else:
            icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/add.png")
            addStyleToLayerAction = QtGui.QAction(icon, "Add style to layer...", explorer)
            addStyleToLayerAction.triggered.connect(lambda: self.addStyleToLayer(explorer))
            actions.append(addStyleToLayerAction)
            icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/delete.gif")
            deleteLayerAction = QtGui.QAction(icon, "Delete", explorer)
            deleteLayerAction.triggered.connect(lambda: self.deleteLayer(tree, explorer))
            actions.append(deleteLayerAction)
            icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/import_into_qgis.png")
            addLayerAction = QtGui.QAction(icon, "Add to current QGIS project", explorer)
            addLayerAction.triggered.connect(lambda: self.addLayerToProject(explorer))
            actions.append(addLayerAction)

        return actions

    def multipleSelectionContextMenuActions(self, tree, explorer, selected):
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/delete.gif")
        deleteSelectedAction = QtGui.QAction(icon, "Delete", explorer)
        deleteSelectedAction.triggered.connect(lambda: self.deleteElements(selected, tree, explorer))
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/group.gif")
        createGroupAction = QtGui.QAction(icon, "Create group...", explorer)
        createGroupAction.triggered.connect(lambda: self.createGroupFromLayers(selected, tree, explorer))
        return [deleteSelectedAction, createGroupAction]


    def createGroupFromLayers(self, selected, tree, explorer):
        name, ok = QtGui.QInputDialog.getText(None, "Group name", "Enter the name of the group to create")
        if not ok:
            return
        catalog = self.element.catalog
        catalogItem = tree.findAllItems(catalog)[0]
        if catalogItem:
            groupsItem = catalogItem.groupsItem
        else:
            groupsItem = None
        layers = [item.element for item in selected]
        styles = [layer.default_style.name for layer in layers]
        layerNames = [layer.name for layer in layers]
        #TODO calculate bounds
        bbox = None
        group =  UnsavedLayerGroup(catalog, name, layerNames, styles, bbox)

        explorer.run(self.parentCatalog().save,
                     "Create group '" + name + "'",
                     [groupsItem],
                     group)

    def deleteLayer(self, tree, explorer):
        self.deleteElements([self], tree, explorer)

    def removeLayerFromGroup(self, explorer):
        group = self.parent().element
        layers = group.layers
        styles = group.styles
        idx = group.layers.index(self.element.name)
        del layers[idx]
        del styles[idx]
        group.dirty.update(layers = layers, styles = styles)
        explorer.run(self.parentCatalog().save,
                 "Remove layer '" + self.element.name + "' from group '" + group.name +"'",
                 [self.parent()],
                 group)

    def moveLayerDownInGroup(self, explorer):
        group = self.parent().element
        layers = group.layers
        styles = group.styles
        idx = group.layers.index(self.element.name)
        tmp = layers [idx + 1]
        layers[idx + 1] = layers[idx]
        layers[idx] = tmp
        tmp = styles [idx + 1]
        styles[idx + 1] = styles[idx]
        styles[idx] = tmp
        group.dirty.update(layers = layers, styles = styles)
        explorer.run(self.parentCatalog().save,
                 "Move layer '" + self.element.name + "' down in group '" + group.name +"'",
                 [self.parent()],
                 group)

    def moveLayerToBackInGroup(self, explorer):
        group = self.parent().element
        layers = group.layers
        styles = group.styles
        idx = group.layers.index(self.element.name)
        tmp = layers[idx]
        del layers[idx]
        layers.insert(0, tmp)
        tmp = styles [idx]
        del styles[idx]
        styles.insert(0, tmp)
        group.dirty.update(layers = layers, styles = styles)
        explorer.run(self.parentCatalog().save,
                 "Move layer '" + self.element.name + "' to front in group '" + group.name +"'",
                 [self.parent()],
                 group)

    def moveLayerToFrontInGroup(self, explorer):
        group = self.parent().element
        layers = group.layers
        styles = group.styles
        idx = group.layers.index(self.element.name)
        tmp = layers[idx]
        del layers[idx]
        layers.append(tmp)
        tmp = styles [idx]
        del styles[idx]
        styles.append(tmp)
        group.dirty.update(layers = layers, styles = styles)
        explorer.run(self.parentCatalog().save,
                 "Move layer '" + self.element.name + "' to back in group '" + group.name +"'",
                 [self.parent()],
                 group)

    def moveLayerUpInGroup(self, explorer):
        group = self.parent().element
        layers = group.layers
        styles = group.styles
        idx = group.layers.index(self.element.name)
        tmp = layers [idx - 1]
        layers[idx - 1] = layers[idx]
        layers[idx] = tmp
        tmp = styles [idx - 1]
        styles[idx - 1] = styles[idx]
        styles[idx] = tmp
        group.dirty.update(layers = layers, styles = styles)
        explorer.run(self.parentCatalog().save,
                 "Move layer '" + self.element.name + "' up in group '" + group.name +"'",
                 [self.parent()],
                 group)


    def addStyleToLayer(self, explorer):
        cat = self.parentCatalog()
        layer = self.element
        dlg = AddStyleToLayerDialog(cat, layer)
        dlg.exec_()
        if dlg.style is not None:
            styles = layer.styles
            default = layer.default_style
            if dlg.default or default is None:
                if default:
                    # copy it to additional styles
                    styles.append(default)
                    layer.styles = styles
                layer.default_style = dlg.style
            else:
                styles.append(dlg.style)
                layer.styles = styles
            return explorer.run(
                cat.save,
                "Add style '" + dlg.style.name + "' to layer '" + layer.name + "'",
                [self],
                layer)
        else:
            return False

    def addLayerToProject(self, explorer):
        #Using threads here freezes the QGIS GUI
        #TODO: fix this
        cat = CatalogWrapper(self.parentCatalog())
        try:
            cat.addLayerToProject(self.element.name)
            explorer.setInfo("Layer '" + self.element.name + "' correctly added to QGIS project")
        except Exception, e:
            explorer.setError(str(e))


class GsGroupItem(GsTreeItem):
    def __init__(self, group):
        self.catalog = group.catalog
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/group.gif")
        GsTreeItem.__init__(self, group, icon)
        self.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
                      | QtCore.Qt.ItemIsDropEnabled)

    def populate(self):
        layers = self.element.catalog.get_layers()
        layersDict = dict([ (layer.name, layer) for layer in layers])
        groupLayers = self.element.layers
        if groupLayers is None:
            return
        for layer in groupLayers:
            if layer is not None:
                if ':' in layer:
                    layer = layer.split(':')[1]
                layerItem = GsLayerItem(layersDict[layer])
                self.addChild(layerItem)


    def acceptDroppedItem(self, tree, explorer, item):
        if isinstance(item, GsLayerItem):
            if self != item.parent():
                addDraggedLayerToGroup(explorer, item.element, self)
                return [self]
            else:
                return []
        else:
            return []

    def contextMenuActions(self, tree, explorer):
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/edit.png")
        editLayerGroupAction = QtGui.QAction(icon, "Edit...", explorer)
        editLayerGroupAction.triggered.connect(lambda: self.editLayerGroup(explorer))
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/delete.gif")
        deleteLayerGroupAction = QtGui.QAction(icon, "Delete", explorer)
        deleteLayerGroupAction.triggered.connect(lambda: self.deleteLayerGroup(tree, explorer))
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/import_into_qgis.png")
        addGroupAction = QtGui.QAction(icon, "Add to current QGIS project", explorer)
        addGroupAction.triggered.connect(lambda: self.addGroupToProject(explorer))
        return [editLayerGroupAction, deleteLayerGroupAction, addGroupAction]


    def multipleSelectionContextMenuActions(self, tree, explorer, selected):
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/delete.gif")
        deleteSelectedAction = QtGui.QAction(icon, "Delete", explorer)
        deleteSelectedAction.triggered.connect(lambda: self.deleteElements(selected, tree, explorer))
        return [deleteSelectedAction]

    def addGroupToProject(self, explorer):
        #Using threads here freezes the QGIS GUI
        #TODO: fix this
        cat = CatalogWrapper(self.parentCatalog())
        try:
            cat.addGroupToProject(self.element.name)
            explorer.setInfo("Group layer '" + self.element.name + "' correctly added to QGIS project")
        except Exception, e:
            explorer.setError(str(e))

    def deleteLayerGroup(self, tree, explorer):
        self.deleteElements([self], tree, explorer);

    def editLayerGroup(self, explorer):
        cat = self.parentCatalog()
        dlg = LayerGroupDialog(cat, self.element)
        dlg.exec_()
        group = dlg.group
        if group is not None:
            explorer.run(cat.save, "Edit layer group '" + self.element.name + "'",
                              [self],
                              group)


class GsStyleItem(GsTreeItem):
    def __init__(self, style, isDefault):
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/style.png")
        name = style.name if not isDefault else style.name + " [default style]"
        GsTreeItem.__init__(self, style, icon, name)
        self.isDefault = isDefault
        self.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable |
                      QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled)

    def contextMenuActions(self, tree, explorer):
        actions = []
        if isinstance(self.parent(), GsLayerItem):
            icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/default-style.png")
            setAsDefaultStyleAction = QtGui.QAction(icon, "Set as default style", explorer)
            setAsDefaultStyleAction.triggered.connect(lambda: self.setAsDefaultStyle(tree, explorer))
            setAsDefaultStyleAction.setEnabled(not self.isDefault)
            actions.append(setAsDefaultStyleAction)
            icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/delete.gif")
            removeStyleFromLayerAction = QtGui.QAction(icon, "Remove style from layer", explorer)
            removeStyleFromLayerAction.triggered.connect(lambda: self.removeStyleFromLayer(tree, explorer))
            removeStyleFromLayerAction.setEnabled(not self.isDefault)
            actions.append(removeStyleFromLayerAction)
            icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/edit.png")
            editStyleAction = QtGui.QAction(icon, "Edit...", explorer)
            editStyleAction.triggered.connect(lambda: self.editStyle(tree, explorer, self.parent().element))
            actions.append(editStyleAction)
        else:
            icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/delete.gif")
            deleteStyleAction = QtGui.QAction(icon, "Delete", explorer)
            deleteStyleAction.triggered.connect(lambda: self.deleteStyle(tree, explorer))
            actions.append(deleteStyleAction)
            icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/edit.png")
            editStyleAction = QtGui.QAction(icon, "Edit...", explorer)
            editStyleAction.triggered.connect(lambda: self.editStyle(tree, explorer))
            actions.append(editStyleAction)
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/edit_sld.png")
        editSLDAction = QtGui.QAction(icon, "Edit SLD...", explorer)
        editSLDAction.triggered.connect(lambda: self.editSLD(tree, explorer))
        actions.append(editSLDAction)
        return actions


    def acceptDroppedItem(self, tree, explorer, item):
        if isinstance(item, GsStyleItem):
            if isinstance(self.parent(), GsLayerItem):
                destinationItem = self.parent()
                addDraggedStyleToLayer(tree, explorer, item, destinationItem)
        return []

    def multipleSelectionContextMenuActions(self, tree, explorer, selected):
        if isinstance(selected[0].parent(), GsLayerItem):
            default = any([s.isDefault for s in selected])
            if not default:
                icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/delete.gif")
                deleteSelectedAction = QtGui.QAction(icon, "Remove from layer", explorer)
                deleteSelectedAction.triggered.connect(lambda: self.removeStylesFromLayer(selected, tree, explorer))
                return [deleteSelectedAction]
            else:
                return []
        else:
            icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/delete.gif")
            deleteSelectedAction = QtGui.QAction(icon, "Delete", explorer)
            deleteSelectedAction.triggered.connect(lambda: self.deleteElements(selected, tree, explorer))
            return [deleteSelectedAction]

    def editStyle(self, tree, explorer, gslayer = None):
        settings = QtCore.QSettings()
        prjSetting = settings.value('/Projections/defaultBehaviour')
        settings.setValue('/Projections/defaultBehaviour', '')
        if gslayer is None:
            gslayer = getLayerFromStyle(self.element)
        if gslayer is not None:
            if not hasattr(gslayer.resource, "attributes"):
                QtGui.QMessageBox.warning(explorer, "Edit style", "Editing raster layer styles is currently not supported")
                return
        sld = self.element.sld_body
        sld = adaptGsToQgs(sld)
        sldfile = tempFilename("sld")
        with open(sldfile, 'w') as f:
            f.write(sld)
        geomtype = getGeomTypeFromSld(sld)
        uri = geomtype + "?crs=epsg:4326&"
        if gslayer is not None:
            fields = gslayer.resource.attributes
            fieldsdesc = ['field=%s:double' % f for f in fields if "geom" not in f]
            fieldsstring = '&'.join(fieldsdesc)
            uri += fieldsstring
        layer = QgsVectorLayer(uri, "tmp", "memory")
        layer.loadSldStyle(sldfile)
        oldSld = getGsCompatibleSld(layer)[0]
        config.iface.showLayerProperties(layer)
        settings.setValue('/Projections/defaultBehaviour', prjSetting)
        newSld = getGsCompatibleSld(layer)[0]
        #TODO: we are not considering the possibility of the user selecting new svg markers,
        #      which would need to be uploaded
        if newSld != oldSld:
            explorer.run(self.element.update_body, "Update style", [], newSld)

    def editSLD(self, tree, explorer):
        dlg = SldEditorDialog(self.element, explorer)
        dlg.exec_()

    def deleteStyle(self, tree, explorer):
        self.deleteElements([self], tree, explorer)

    def removeStyleFromLayer(self, tree, explorer):
        layer = self.parent().element
        styles = layer.styles
        styles = [style for style in styles if style.name != self.element.name]
        layer.styles = styles
        explorer.run(self.parentCatalog().save,
                "Remove style '" + self.element.name + "' from layer '" + layer.name,
                tree.findAllItems(self.parent().element),
                layer)

    def removeStylesFromLayer(self, selected, tree, explorer):
        catalog = self.parentCatalog()
        layerStyles = defaultdict(list)
        for item in selected:
            layerStyles[item.parent()].append(item.element.name)
        for layerItem, styles in layerStyles.iteritems():
            layer = layerItem.element
            currentStyles = layer.styles
            currentStyles = [style for style in styles if style not in styles]
            layer.styles = currentStyles
            explorer.run(catalog.save,
                    "Remove style '" + self.element.name + "' from layer '" + layer.name,
                    [layerItem],
                    layer)

    def setAsDefaultStyle(self, tree, explorer):
        layer = self.parent().element
        styles = layer.styles
        styles = [style for style in styles if style.name != self.element.name]
        default = layer.default_style
        if default is not None:
            styles.append(default)
        layer.default_style = self.element
        layer.styles = styles
        def _saveAndRefresh():
            self.parentCatalog().save(layer)
            layer.refresh()
        explorer.run(_saveAndRefresh,
                "Set style '" + self.element.name + "' as default style for layer '" + layer.name + "'",
                [self.parent()])


class GsWorkspaceItem(GsTreeItem):
    def __init__(self, workspace, isDefault):
        self.catalog = workspace.catalog
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/workspace.png")
        self.isDefault = isDefault
        name = workspace.name if not isDefault else workspace.name + " [default workspace]"
        GsTreeItem.__init__(self, workspace, icon, name)
        self.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDropEnabled)

    def populate(self):
        stores = self.element.catalog.get_stores(self.element)
        for store in stores:
            storeItem = GsStoreItem(store)
            storeItem.populate()
            self.addChild(storeItem)


    def contextMenuActions(self, tree, explorer):
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/default-workspace.png")
        setAsDefaultAction = QtGui.QAction(icon, "Set as default workspace", explorer)
        setAsDefaultAction.triggered.connect(lambda: self.setAsDefaultWorkspace(tree, explorer))
        setAsDefaultAction.setEnabled(not self.isDefault)
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/delete.gif")
        deleteWorkspaceAction = QtGui.QAction(icon, "Delete", explorer)
        deleteWorkspaceAction.triggered.connect(lambda: self.deleteWorkspace(tree, explorer))
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/clean.png")
        cleanAction = QtGui.QAction(icon, "Clean (remove unused resources)", explorer)
        cleanAction.triggered.connect(lambda: self.cleanWorkspace(explorer))
        return[setAsDefaultAction, deleteWorkspaceAction, cleanAction]

    def cleanWorkspace(self, explorer):
        cat = CatalogWrapper(self.catalog)
        explorer.run(cat.cleanUnusedResources, "Clean (remove unused resources)", [self])

    def multipleSelectionContextMenuActions(self, tree, explorer, selected):
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/delete.gif")
        deleteSelectedAction = QtGui.QAction(icon, "Delete", explorer)
        deleteSelectedAction.triggered.connect(lambda: self.deleteElements(selected, tree, explorer))
        return [deleteSelectedAction]

    def deleteWorkspace(self, tree, explorer):
        self.deleteElements([self], tree, explorer)

    def setAsDefaultWorkspace(self, tree, explorer):
        parent = self.parent()
        expanded = self.isExpanded()
        if explorer.run(self.parentCatalog().set_default_workspace,
                        "Set workspace '" + self.element.name + "' as default workspace",
                        [self.parent()],
                        self.element.name):

            wsitem = parent  # fallback clicked item, to refresh toolbar
            items = [parent.child(i) for i in range(0, parent.childCount())]
            for item in items:
                if (isinstance(item, GsWorkspaceItem)
                        and hasattr(item, 'isDefault')):
                    if item.isDefault:
                        wsitem = item
                        break

            tree.setItemSelected(wsitem, True)
            tree.treeItemClicked(wsitem, 0)
            # all stores and other workspaces collapse
            wsitem.setExpanded(expanded)

    def acceptDroppedUris(self, tree, explorer, uris):
        return addDraggedUrisToWorkspace(uris, self.parentCatalog(), self.element, explorer, tree)

class GsStoreItem(GsTreeItem):
    def __init__(self, store):
        if isinstance(store, DataStore):
            icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/layer_polygon.png")
        else:
            icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/grid.jpg")
        GsTreeItem.__init__(self, store, icon)
        self.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDropEnabled)

    def populate(self):
        resources = self.element.get_resources()
        for resource in resources:
            resourceItem = GsResourceItem(resource)
            self.addChild(resourceItem)

    def contextMenuActions(self, tree, explorer):
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/delete.gif")
        deleteStoreAction = QtGui.QAction(icon, "Delete", explorer)
        deleteStoreAction.triggered.connect(lambda: self.deleteStore(tree, explorer))
        return[deleteStoreAction]

    def multipleSelectionContextMenuActions(self, tree, explorer, selected):
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/delete.gif")
        deleteSelectedAction = QtGui.QAction(icon, "Delete", explorer)
        deleteSelectedAction.triggered.connect(lambda: self.deleteElements(selected, tree, explorer))
        return [deleteSelectedAction]

    def deleteStore(self, tree, explorer):
        self.deleteElements([self], tree, explorer)

    def _getDescriptionHtml(self, tree, explorer):
        html = '<p><h3><b>Properties</b></h3></p><ul>'
        html += '<li>Store type: %s</li></ul>' % self.element.type
        actions = self.contextMenuActions(tree, explorer)
        items = tree.selectedItems()
        if len(items) > 1:
            actions = self.multipleSelectionContextMenuActions(
                tree, explorer, items)
        actsenabled = [act for act in actions if act.isEnabled()]
        if actsenabled:
            html += "<p><b>Available actions</b></p><ul>"
            for action in actsenabled:
                html += '<li><a href="' + action.text() + '">' + action.text() + '</a></li>\n'
            html += '</ul>'
        return html

class GsResourceItem(GsTreeItem):
    def __init__(self, resource):
        if isinstance(resource, Coverage):
            icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/grid.jpg")
        else:
            icon = None
        GsTreeItem.__init__(self, resource, icon)
        self.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDropEnabled)

    def contextMenuActions(self, tree, explorer):
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/delete.gif")
        deleteResourceAction = QtGui.QAction(icon, "Delete", explorer)
        deleteResourceAction.triggered.connect(lambda: self.deleteResource(tree, explorer))
        return[deleteResourceAction]

    def deleteResource(self, tree, explorer):
        self.deleteElements([self], tree, explorer)





########### WPS #####################

class GsProcessesItem(GsTreeItem):
    def __init__(self, catalog):
        self.catalog = catalog
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/process.png")
        GsTreeItem.__init__(self, None, icon, "WPS processes")
        self.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)

    def populate(self):
        self.element = Wps(self.catalog)
        try:
            processes = self.element.processes()
        except:
            #the WPS extension might not be installed
            processes = []
        for process in processes:
            item = GsProcessItem(process)
            self.addChild(item)


class GsProcessItem(GsTreeItem):
    def __init__(self, process):
        #self.catalog = catalog
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/process.png")
        GsTreeItem.__init__(self, None, icon, process)
        self.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)


################# SETTINGS ###################


class GsSettingsItem(GsTreeItem):
    def __init__(self, catalog):
        self.catalog = catalog
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/../images/config.png")
        settings = Settings(self.catalog)
        GsTreeItem.__init__(self, settings, icon, "Settings")
        self.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)

    def descriptionWidget(self, tree, explorer):
        self.description = ParameterEditor(self.element, explorer)
        return self.description

class GsSettingItem(GsTreeItem):
    def __init__(self, settings, name, value):
        self.catalog = settings.catalog
        GsTreeItem.__init__(self, None, None, name)
        self.setText(1, value)
        self.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)

