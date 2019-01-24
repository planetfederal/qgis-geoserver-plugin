# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
from geoserverexplorer.geoserver import util
from qgis.PyQt import QtGui, QtCore, QtWidgets

class TreeItem(QtWidgets.QTreeWidgetItem):
    def __init__(self, element, icon = None, text = None):
        QtWidgets.QTreeWidgetItem.__init__(self)
        self.element = element
        self.setData(0, QtCore.Qt.UserRole, element)
        self._text = text
        text = text if text is not None else util.name(element)
        self.setText(0, text)
        if icon is not None:
            self.setIcon(0, icon)
        self.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)

    def refresh(self):
        text = self._text if self._text is not None else util.name(self.element)
        self.setText(0, text)

    def refreshContent(self, explorer):
        self.takeChildren()
        self.refresh()
        if hasattr(self, 'populate'):
            explorer.run(self.populate, None, [])

    def descriptionWidget(self, tree, explorer):
        text = self.getDescriptionHtml(tree, explorer)
        class MyBrowser(QtWidgets.QTextBrowser):
            def loadResource(self, type, name):
                return None
        self.description = MyBrowser()
        self.description.setOpenLinks(False)
        def linkClicked(url):
            self.linkClicked(tree, explorer, url)
        self.description.anchorClicked.connect(linkClicked)
        self.description.setHtml(text)
        return self.description

    def getDescriptionHtml(self, tree, explorer):
        typesok, html = self._checkAllSelectionTypes(self, tree)
        if typesok:
            html += self._getDescriptionHtml(tree, explorer)
        txt = self.text(0)
        items = tree.selectedItems()
        if len(items) > 1:
            txt = "Multiple Selection"
        img = ""
        if hasattr(self, "iconPath"):
            img = '<img src="' + self.iconPath() + '"/>'
        header = u'<div style="background-color:#C7DBFC;"><h1>&nbsp; ' + img + "&nbsp;" + txt + '</h1></div>'
        html = u"""
            <!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
            <html>
            <head>
            <style type="text/css">
                h1 { color: #555555}
                a { text-decoration: none; color: #3498db; font-weight: bold; }
                a.edit { color: #9f9f9f; float: right; font-weight: normal; }
                p { color: #666666; }
                b { color: #333333; }
                .section { margin-top: 25px; }
                table.header th { background-color: #dddddd; }
                table.header td { background-color: #f5f5f5; }
                table.header th, table.header td { padding: 0px 10px; }
                table td { padding-right: 20px; }
                .underline { text-decoration:underline; }
            </style>
            </head>
            <body>
            %s %s <br>
            </body>
            </html>
            """ % (header, html)
        return html

    def _getDescriptionHtml(self, tree, explorer):
        html = ""
        typesok, typesmsg = self._checkAllSelectionTypes(self, tree)
        if not typesok:
            return typesmsg
        else:
            html += typesmsg
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
        actions = self.contextMenuActions(tree, explorer)
        items = tree.selectedItems()
        if len(items) > 1:
            actions = self.multipleSelectionContextMenuActions(
                tree, explorer, items)
        for action in actions:
            if action.text() == actionName:
                action.trigger()
                return

    def _checkAllSelectionTypes(self, item, tree):
        allTypes, allParentTypes = tree.getSelectionTypes()
        if (allTypes and len(allTypes) != 1) or (allParentTypes and len(allParentTypes) != 1):
            return False, "Incompatible item types"
        items = tree.selectedItems()
        if len(items) > 1 and tree.currentItem() in items:
            return True, "<h3><b>Current item:</b> <em>{0}</em></h3>".format(item.text(0))
        return True, ""

    def contextMenuActions(self, tree, explorer):
        return []

    def multipleSelectionContextMenuActions(self, tree, explorer, selected):
        return []

    def acceptDroppedItem(self, tree, explorer, item):
        return []

    def acceptDroppedItems(self, tree, explorer, items):
        if len(items) > 1:
            explorer.setProgressMaximum(len(items))
        toUpdate = []
        try:
            for i, item in enumerate(items):
                toUpdate.extend(self.acceptDroppedItem(tree, explorer, item))
                explorer.setProgress(i + 1)
        finally:
            explorer.resetActivity()
            return toUpdate

    def acceptDroppedUris(self, tree, explorer, uris):
        return []
