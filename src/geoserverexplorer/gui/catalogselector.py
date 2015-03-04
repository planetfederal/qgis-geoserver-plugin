from PyQt4 import QtGui

def selectCatalog(catalogs):
    if len(catalogs) == 1:
        return catalogs.values()[0]
    elif len(catalogs) == 0:
        return None
    else:
        item, ok = QtGui.QInputDialog.getItem(None,
                    "Catalog selection",
                    "Select a destination catalog",
                    catalogs.keys(),
                    editable = False)
        if ok:
            return catalogs[item]
        else:
            return None
        