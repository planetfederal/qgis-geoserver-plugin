# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
from zipfile import ZipFile
import tempfile
from os import path


def name(named):
    """Get the name out of an object.  This varies based on the type of the input:
       * the "name" of a string is itself
       * the "name" of None is itself
       * the "name" of an object with a property named name is that property -
         as long as it's a string
       * otherwise, we raise a ValueError
    """
    if isinstance(named, str) or named is None:
        return named
    elif hasattr(named, 'name'):
        if isinstance(named.name, str):
            return named.name
        elif callable(named.name) and isinstance(named.name(), str):
            return named.name()    
    else:
        raise ValueError("Can't interpret %s as a name or a configuration object" % named)
    
def getLayerFromStyle(style):
    '''Tries to find out which layer is using a given style.
    Returns none if cannot find a layer using the style'''
    cat = style.catalog
    layers = cat.get_layers()
    for layer in layers:
        if layer.default_style.name == style.name:
            return layer
        alternateStyles = layer.styles
        for alternateStyle in alternateStyles:
            if style.name == alternateStyle.name:
                return layer
    
def groupsWithLayer(catalog, layer):
    grps = catalog.get_layergroups()
    grpswlyr = []
    for grp in grps:
        lyrs = grp.layers
        if lyrs is None:
            continue
        for lyr in lyrs:
            if layer.name == lyr:
                grpswlyr.append(grp)
                break
    return grpswlyr

def removeLayerFromGroups(catalog, layer, groups=None):
    grps = groups or catalog.get_layergroups()
    for grp in grps:
        lyrs = grp.layers
        if lyrs is None:
            continue
        if layer.name not in lyrs:
            continue
        styles = grp.styles
        idx = lyrs.index(layer.name)
        del lyrs[idx]
        del styles[idx]
        grp.dirty.update(layers=lyrs, styles=styles)
        catalog.save(grp)

def addLayerToGroups(catalog, layer, groups, workspace=None):
    '''This assumes the layer style with same name as layer already exists,
    otherwise None is assigned'''
    for grp in groups:
        lyrs = grp.layers
        styles = grp.styles
        lyrs.append(layer.name)
        style = catalog.get_styles(layer.name, workspace=workspace)[0]
        styles.append(style)
        grp.dirty.update(layers=lyrs, styles=styles)
        catalog.save(grp)
