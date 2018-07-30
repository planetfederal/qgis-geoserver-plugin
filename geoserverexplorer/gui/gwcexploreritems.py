# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *
from geoserverexplorer.gui.dialogs.gwclayer import EditGwcLayerDialog, SeedGwcLayerDialog
from geoserverexplorer.geoserver.gwc import Gwc, GwcLayer, SeedingStatusParsingError
from geoserver.catalog import FailedRequestError
from geoserverexplorer.gui.exploreritems import TreeItem
import os
from geoserverexplorer.gui.confirm import confirmDelete

class GwcTreeItem(TreeItem):

    def iconPath(self):
        return os.path.dirname(__file__) + "/../images/gwc.png"

class GwcLayersItem(GwcTreeItem):
    def __init__(self, catalog):
        self.catalog = catalog
        icon = QIcon(os.path.dirname(__file__) + "/../images/gwc.png")
        TreeItem.__init__(self, None, icon, "GeoWebCache layers")
        self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDropEnabled)

    def populate(self):
        try:
            catalog = self.catalog
            self.element = Gwc(catalog)
            layers = self.element.layers()
            for layer in layers:
                item = GwcLayerItem(layer)
                self.addChild(item)
            self.isValid = True
        except:
            raise
            self.takeChildren()
            self.isValid = False

    def acceptDroppedItem(self, tree, explorer, item):
        if self.isValid:
            from geoserverexplorer.gui.gsexploreritems import GsLayerItem
            if isinstance(item, GsLayerItem):
                if createGwcLayer(explorer, item.element):
                    return [self]
            else:
                return []
        else:
            return []

    def contextMenuActions(self, tree, explorer):
        if self.isValid:
            icon = QIcon(os.path.dirname(__file__) + "/../images/add.png")
            addGwcLayerAction = QAction(icon, "New GWC layer...", explorer)
            addGwcLayerAction.triggered.connect(lambda: self.addGwcLayer(tree, explorer))
            return [addGwcLayerAction]
        else:
            return []


    def addGwcLayer(self, tree, explorer):
        cat = self.catalog
        layers = cat.get_layers()
        if layers:
            dlg = EditGwcLayerDialog(layers, None)
            dlg.exec_()
            if dlg.gridsets is not None:
                layer = dlg.layer
                gwc = Gwc(layer.catalog)
                gwclayer = GwcLayer(gwc, layer.name, dlg.formats, dlg.gridsets, dlg.metaWidth, dlg.metaHeight)
                catItem = tree.findAllItems(cat)[0]
                explorer.run(gwc.addLayer,
                                  "Create GWC layer '" + layer.name + "'",
                                  [catItem.gwcItem],
                                  gwclayer)
        else:
            QMessageBox.warning(None, "Create GWC layer", "There are no layers in the catalog")

class GwcLayerItem(GwcTreeItem):
    def __init__(self, layer):
        icon = QIcon(os.path.dirname(__file__) + "/../images/layer.png")
        TreeItem.__init__(self, layer, icon)
        self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDropEnabled)

    def contextMenuActions(self, tree, explorer):
        icon = QIcon(os.path.dirname(__file__) + "/../images/edit.png")
        editGwcLayerAction = QAction(icon, "Edit...", explorer)
        editGwcLayerAction.triggered.connect(lambda: self.editGwcLayer(explorer))
        icon = QIcon(os.path.dirname(__file__) + "/../images/seed.png")
        seedGwcLayerAction = QAction(icon, "Seed...", explorer)
        seedGwcLayerAction.triggered.connect(lambda: self.seedGwcLayer(explorer))
        emptyGwcLayerAction = QAction("Empty", explorer)
        emptyGwcLayerAction.triggered.connect(lambda: self.emptyGwcLayer(explorer))
        icon = QIcon(os.path.dirname(__file__) + "/../images/delete.gif")
        deleteLayerAction = QAction(icon, "Delete", explorer)
        deleteLayerAction.triggered.connect(lambda: self.deleteLayer(explorer))
        return[editGwcLayerAction, seedGwcLayerAction, emptyGwcLayerAction, deleteLayerAction]

    def acceptDroppedItem(self, tree, explorer, item):
        from geoserverexplorer.gui.gsexploreritems import GsLayerItem
        if isinstance(item, GsLayerItem):
            if createGwcLayer(explorer, item.element):
                return [self.parent()]
        else:
            return []

    def multipleSelectionContextMenuActions(self, tree, explorer, selected):
        icon = QIcon(os.path.dirname(__file__) + "/../images/delete.gif")
        deleteSelectedAction = QAction(icon, "Delete", explorer)
        deleteSelectedAction.triggered.connect(lambda: self.deleteLayers(explorer, selected))
        return [deleteSelectedAction]


    def _getDescriptionHtml(self, tree, explorer):
        html = ""
        typesok, typesmsg = self._checkAllSelectionTypes(self, tree)
        if not typesok:
            return typesmsg
        else:
            html += typesmsg

        items = tree.selectedItems()
        # don't show if multiple items selected, but not the current item
        if not items or self in items or len(items) == 1:
            try:
                html += '<p><b>Seeding status</b></p>'
                state = self.element.getSeedingState()
                if state is None:
                    html += "<p>No seeding tasks exist for this layer</p>"
                else:
                    html += "<p>This layer is being seeded. Processed {} tiles of {}</p>".format(state[0], state[1])
                    html += '<p><a href="update">update</a> - <a href="kill">kill</a></p>'
            except SeedingStatusParsingError:
                html += '<p>Cannot determine running seeding tasks for this layer</p>'
            except:
                html = "<p><b>Could not get information from server. Try refreshing the item to update this description panel</b></p>"

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


    def linkClicked(self, tree, explorer, url):
        TreeItem.linkClicked(self,tree, explorer, url)
        if url.toString() == 'kill':
            try:
                self.element.killSeedingTasks()
            except FailedRequestError:
                #TODO:
                return
        try:
            text = self.getDescriptionHtml(tree, explorer)
            self.description.setHtml(text)
        except:
            explorer.setDescriptionWidget()


    def deleteLayer(self, explorer):
        self.deleteLayers(explorer, [self])

    def deleteLayers(self, explorer, items):
        if not confirmDelete():
            return
        explorer.setProgressMaximum(len(items), "Deleting GWC layers")
        toUpdate = []
        for i, item in enumerate(items):
            explorer.run(item.element.delete,
                     None,
                     [])
            explorer.setProgress(i)
            if item.parent() not in toUpdate:
                toUpdate.append(item.parent())
        for item in toUpdate:
            if item is not None:
                item.refreshContent(explorer)
        if None in toUpdate:
            explorer.refreshContent()
        explorer.resetActivity()
        explorer.setDescriptionWidget()


    def emptyGwcLayer(self, explorer):
        layer = self.element
        #TODO: confirmation dialog??
        explorer.run(layer.truncate,
                      "Truncate GWC layer '" + layer.name + "'",
                      [],
                      )
    def seedGwcLayer(self, explorer):
        layer = self.element
        dlg = SeedGwcLayerDialog(layer)
        dlg.show()
        dlg.exec_()
        if dlg.format is not None:
            explorer.run(layer.seed,
                          "Request seed for GWC layer '" + layer.name + "' ",
                          [],
                          dlg.operation, dlg.format, dlg.gridset, dlg.minzoom, dlg.maxzoom, dlg.extent)

    def editGwcLayer(self, explorer):
        layer = self.element
        dlg = EditGwcLayerDialog([layer], layer)
        dlg.exec_()
        if dlg.gridsets is not None:
            explorer.run(layer.update,
                          "Update GWC layer '" + layer.name + "'",
                          [],
                          dlg.formats, dlg.gridsets, dlg.metaWidth, dlg.metaHeight)




def createGwcLayer(explorer, layer):
    dlg = EditGwcLayerDialog([layer], None)
    dlg.exec_()
    if dlg.gridsets is not None:
        gwc = Gwc(layer.catalog)
        gwclayer = GwcLayer(gwc, layer.name, dlg.formats, dlg.gridsets, dlg.metaWidth, dlg.metaHeight)
        explorer.run(gwc.addLayer,
                          "Create GWC layer '" + layer.name + "'",
                          [],
                          gwclayer)
        return True
    else:
        return False
