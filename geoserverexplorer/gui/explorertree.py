# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
import os
from qgis.core import *
from geoserverexplorer.gui.gsexploreritems import *
from geoserverexplorer.qgis.layers import *
from geoserverexplorer.qgis import uri as uri_utils
from qgis.PyQt import QtXml
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtWidgets import QMessageBox
from geoserver.catalog import FailedRequestError

class ExplorerTreeWidget(QTreeWidget):

    def __init__(self, explorer):
        self.explorer = explorer
        QTreeWidget.__init__(self, None)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setColumnCount(1)
        self.header().hide()
        self.currentItemChanged.connect(self.highlightCurrentItem)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showTreePopupMenu)
        self.itemExpanded.connect(self.treeItemExpanded)
        self.itemClicked.connect(self.treeItemClicked)
        self.itemDoubleClicked.connect(self.treeItemDoubleClicked)
        self.setDragDropMode(QTreeWidget.DragDrop)
        self.setAutoScroll(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.lastClicked = None

        self.itemSelectionChanged.connect(
            lambda : self._selectionChanged(explorer))
        self.fillData()

    def fillData(self):
        self.gsItem = GsCatalogsItem()
        self.addTopLevelItem(self.gsItem)

    def highlightCurrentItem(self, cur, prev):
        if cur == prev:
            return
        def highlight(item, h):
            f = item.font(0)
            f.setUnderline(h)
            item.setFont(0, f)
        if prev:
            highlight(prev, False)
        if cur:
            highlight(cur, True)

    def getSelectionTypes(self):
        items = self.selectedItems()
        types = set([type(item) for item in items])
        parentTypes = set([type(item.parent()) for item in items])
        return types, parentTypes

    def treeItemClicked(self, item, column):
        # handle situation where actions act on current clicked item, but single
        # selection of another item leads user to think that is being acted upon
        # fix: when a single selection is created that is not the current item,
        #      make it the current item, as if the user had clicked only it
        # NOTE: without a proper model/view setup, this hack is required, unless
        #       the whole plugin is refactored to work only upon tree selection
        # see also: self._selectionChanged
        items = self.selectedItems()
        if len(items) == 1 and self.currentItem() not in items:
            self.setCurrentItem(items[0], 0, QItemSelectionModel.Current)
            self.treeItemClicked(items[0], 0)
            return

        self.lastClicked = item
        if hasattr(item, 'descriptionWidget'):
            try:
                widget = item.descriptionWidget(self, self.explorer)
            except FailedRequestError:
                QMessageBox.warning(self, "Error retrieving element description",
                                    "The element description cannot be retrieved.\nThe selected element might have been deleted.")
                self.explorer.refreshContent()
                return
            if widget is not None:
                self.explorer.setDescriptionWidget(widget)
        actions = item.contextMenuActions(self, self.explorer)
        if len(items) > 1:
            actions = item.multipleSelectionContextMenuActions(
                self, self.explorer, items)
        if (isinstance(item, TreeItem)):
            icon = QIcon(os.path.dirname(__file__) + "/../images/refresh.png")
            refreshAction = QAction(icon, "Refresh", self.explorer)
            refreshAction.triggered.connect(lambda: item.refreshContent(self.explorer))
            actions.append(refreshAction)
        self.explorer.setToolbarActions(actions)

    def treeItemDoubleClicked(self, item, column):
        if not isinstance(item, TreeItem):
            return
        actions = item.contextMenuActions(self, self.explorer)
        for action in actions:
            if "edit" in action.text().lower():
                action.trigger()
                return

    def lastClickedItem(self):
        return self.lastClicked

    def treeItemExpanded(self, item):
        if item is not None and not item.childCount():
            item.refreshContent(self.explorer)

    def showTreePopupMenu(self,point):
        allTypes, allParentTypes = self.getSelectionTypes()
        if len(allTypes) != 1 or len(allParentTypes) != 1:
            return
        items = self.selectedItems()
        if len(items) > 1:
            self.showMultipleSelectionPopupMenu(point)
        else:
            self.showSingleSelectionPopupMenu(point)

    def getDefaultWorkspace(self, catalog):
        workspaces = catalog.get_workspaces()
        if workspaces:
            return catalog.get_default_workspace()
        else:
            return None

    def showMultipleSelectionPopupMenu(self, point):
        self.selectedItem = self.itemAt(point)
        point = self.mapToGlobal(point)
        menu = QMenu()
        actions = self.selectedItem.multipleSelectionContextMenuActions(self, self.explorer, self.selectedItems())
        for action in actions:
            menu.addAction(action)
        menu.exec_(point)


    def showSingleSelectionPopupMenu(self, point):
        self.selectedItem = self.itemAt(point)
        if not isinstance(self.selectedItem, TreeItem):
            return
        menu = QMenu()
        if (isinstance(self.selectedItem, TreeItem) and hasattr(self.selectedItem, 'populate')):
            refreshIcon = QIcon(os.path.dirname(__file__) + "/../images/refresh.png")
            refreshAction = QAction(refreshIcon, "Refresh", None)
            refreshAction.triggered.connect(lambda: self.selectedItem.refreshContent(self.explorer))
            menu.addAction(refreshAction)
        point = self.mapToGlobal(point)
        actions = self.selectedItem.contextMenuActions(self, self.explorer)
        for action in actions:
            menu.addAction(action)
        menu.exec_(point)

    def findAllItems(self, element):
        allItems = []
        iterator = QTreeWidgetItemIterator(self)
        value = iterator.value()
        while value:
            if hasattr(value, 'element'):
                if hasattr(value.element, 'name') and hasattr(element, 'name'):
                    if  value.element.name == element.name and value.element.__class__ == element.__class__:
                        allItems.append(value)
                elif value.element == element:
                    allItems.append(value)
            iterator += 1
            value = iterator.value()
        #=======================================================================
        # if not allItems:
        #     allItems = [None] #Signal that the whole tree has to be updated
        #=======================================================================
        return allItems

    def _selectionChanged(self, explorer):
        items = self.selectedItems()
        # see also: self.treeItemClicked about single selection workaround
        if (len(items) > 1 and self.currentItem() not in items) \
                or len(items) < 1:
            # reset widget to whatever was the last current item or nothing
            explorer.refreshDescription()



###################################DRAG & DROP########################

    QGIS_URI_MIME = "application/x-vnd.qgis.qgis.uri"
    QGIS_LEGEND_MIME = "application/qgis.layertreemodeldata"


    def mimeTypes(self):
        return ["application/x-qabstractitemmodeldatalist", self.QGIS_URI_MIME, self.QGIS_LEGEND_MIME]

    def mimeData(self, items):
        mimeData = QMimeData()#QTreeWidget.mimeData(self, items)
        encodedData = QByteArray()
        stream = QDataStream(encodedData, QIODevice.WriteOnly)

        for item in items:
            if isinstance(item, GsLayerItem):
                layer = item.element
                uri = uri_utils.layerMimeUri(layer)
                stream.writeQString(uri)

        mimeData.setData(self.QGIS_URI_MIME, encodedData)
        return mimeData

    def dropEvent(self, event):
        items = []
        destinationItem=self.itemAt(event.pos())
        if destinationItem is None:
            return
        if isinstance(event.source(), self.__class__):
            draggedTypes = set([item.__class__ for item in event.source().selectedItems()])
            if len(draggedTypes) > 1:
                return
            items = self.selectedItems()
            toUpdate = destinationItem.acceptDroppedItems(self, self.explorer, items)
        else:
            data = event.mimeData()
            elements = []
            if data.hasUrls():
                for u in data.urls():
                    filename = u.toLocalFile()
                    if filename != "":
                        elements.append(filename)
            if data.hasFormat(self.QGIS_URI_MIME):
                for uri in QgsMimeDataUtils.decodeUriList(data):
                    elements.append(uri)
            elif data.hasFormat(self.QGIS_LEGEND_MIME):
                encodedData = data.data('application/qgis.layertreemodeldata')
                doc = QtXml.QDomDocument()
                if not doc.setContent(encodedData):
                    return
                layerRegistry = QgsProject.instance()
                root = doc.documentElement()
                child = root.firstChildElement()
                while not child.isNull():
                    node = QgsLayerTreeNode.readXML(child)
                    if isinstance(node, QgsLayerTreeLayer):
                        layer = layerRegistry.mapLayer(node.layerId())
                        elements.append(layer.source())
                    else:
                        # publishing layer groups is not supported now
                        continue
                    child = child.nextSiblingElement()

            destinationItem.acceptDroppedUris(self, self.explorer, elements)

        event.setDropAction(Qt.CopyAction)
        event.accept()
