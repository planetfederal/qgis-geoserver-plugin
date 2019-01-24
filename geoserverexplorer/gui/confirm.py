# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
'''
Routines to ask for confirmation when performing certain operations
'''
from builtins import str
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import *
from geoserverexplorer.gui.dialogs.gsnamedialog import getGSLayerName
from geoserverexplorer.gui.gsnameutils import isNameValid, xmlNameRegex
from qgiscommons2.settings import pluginSetting

def publishLayer(catalog, layer, workspace=None, overwrite=False):
    name = layer.name()
    gslayers = [lyr.name for lyr in catalog.catalog.get_layers()]
    # TODO: remove when duplicate names on different workspaces are supported
    #       we shoud check for unique names only on a given workspace
    if (name in gslayers and not overwrite) or not isNameValid(name, gslayers, 0, xmlNameRegex()):
        name = getGSLayerName(name=name, names=gslayers, unique=False)
    catalog.publishLayer(layer, workspace, True, name)


def confirmDelete():
    askConfirmation = pluginSetting("ConfirmDelete")
    if not askConfirmation:
        return True
    msg = "You confirm that you want to delete the selected elements?"
    reply = QMessageBox.question(None, "Delete confirmation",
                                               msg, QMessageBox.Yes |
                                               QMessageBox.No, QMessageBox.No)
    return reply != QMessageBox.No

# noinspection PyPep8Naming
class DeleteDependentsDialog(QDialog):

    def __init__(self, dependent, parent=None):
        super(DeleteDependentsDialog, self).__init__(parent)
        self.title = "Confirm Deletion"
        self.msg = "The following elements depend on the elements to delete " \
                   "and will be deleted as well:"
        typeorder = ['LayerGroup', 'Layer', 'GwcLayer', 'Other']
        names = dict()
        for dep in dependent:
            cls = dep.__class__.__name__
            name = dep.name
            title = ''
            if hasattr(dep, 'resource'):
                if hasattr(dep.resource, 'title'):
                    if dep.resource.title != name:
                        title = dep.resource.title
            desc = "<b>- {0}:</b> &nbsp;{1}{2}".format(
                cls,
                name,
                " ({0})".format(title) if title else ''
            )
            if cls in names:
                names[cls].append(desc)
            else:
                if cls in typeorder:
                    names[cls] = [desc]
                else:
                    if 'Other' in names:
                        names['Other'].append(desc)
                    else:
                        names['Other'] = [desc]

        self.deletes = "<br><br>".join(
            ["<br><br>".join(sorted(list(set(names[typ]))))
             for typ in typeorder if typ in names])
        self.question = "Do you really want to delete all these elements?"
        self.buttonBox = None
        self.initGui()

    def initGui(self):
        self.setWindowTitle(self.title)
        layout = QVBoxLayout()

        msgLabel = QLabel(self.msg)
        msgLabel.setWordWrap(True)
        layout.addWidget(msgLabel)

        deletesView = QTextEdit()
        deletesView.setText(str(self.deletes))
        deletesView.setReadOnly(True)
        deletesView.setLineWrapMode(QTextEdit.NoWrap)
        layout.addWidget(deletesView)

        questLabel = QLabel(self.question)
        questLabel.setWordWrap(True)
        questLabel.setAlignment(Qt.AlignHCenter)
        layout.addWidget(questLabel)

        self.buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(self.buttonBox)

        self.setLayout(layout)
        # noinspection PyUnresolvedReferences
        self.buttonBox.accepted.connect(self.accept)
        # noinspection PyUnresolvedReferences
        self.buttonBox.rejected.connect(self.reject)

        self.setMinimumWidth(400)
        self.setMinimumHeight(400)
        self.resize(500, 400)
