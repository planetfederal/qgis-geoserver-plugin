# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
'''
methods to convert the SLD produced by GeoServer (1.0) to the SLD produced by QGIS (1.1), and also the other way round.
This is a quick and dirty solution until both programs support the same specification
'''

from builtins import hex
from builtins import str
from builtins import range
import re
import os
from qgis.PyQt.QtXml import *
from qgiscommons2.settings import pluginSetting
from qgis.core import *
import math


SIZE_FACTOR = 4
# use this factor (4) in case SLD UOM is NO correctly supported by QGIS
SIZE_FACTOR_IF_NO_UOM = 4 
# use this factor (1) in case SLD UOM is correctly supported by QGIS
SIZE_FACTOR_IF_UOM = 1

RASTER_SLD_TEMPLATE = ('<?xml version="1.0" encoding="UTF-8"?>'
                    '<sld:StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:sld="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:gml="http://www.opengis.''net/gml" version="1.0.0">'
                    '<sld:NamedLayer>'
                    '<sld:Name>STYLE_NAME</sld:Name>'
                    '<sld:UserStyle>'
                    '<sld:Name>STYLE_NAME</sld:Name>'
                    '<sld:Title/>'
                    '<sld:FeatureTypeStyle>'
                    #'<sld:Name>name</sld:Name>'
                    '<sld:Rule>'
                    #'<sld:Name>Single symbol</sld:Name>'
                    '<RasterSymbolizer>'
                    'SYMBOLIZER_CODE'
                    '</RasterSymbolizer>'
                    '</sld:Rule>'
                    '</sld:FeatureTypeStyle>'
                    '</sld:UserStyle>'
                    '</sld:NamedLayer>'
                    '</sld:StyledLayerDescriptor>')

def setScaleFactor():
    """Manage size scale factor basing if QGIS is able to manage or not SLD unit parameter (uom).
    """
    global SIZE_FACTOR
    if pluginSetting("SldUomManaging"):
        SIZE_FACTOR = SIZE_FACTOR_IF_UOM
    else:
        SIZE_FACTOR = SIZE_FACTOR_IF_NO_UOM
        if pluginSetting("SldScaleFactor"):
            SIZE_FACTOR = pluginSetting("SldScaleFactor")

def adaptQgsToGs(sld, layer):
    if layer.type() != QgsMapLayer.VectorLayer:
        return sld, []
    
    setScaleFactor()

    sld = sld.replace("se:SvgParameter","CssParameter")
    sld = sld.replace("1.1.","1.0.")
    sld = sld.replace("\t","")
    sld = sld.replace("\n","")
    sld = re.sub("\s\s+" , " ", sld)
    sld = re.sub("<ogc:Filter>[ ]*?<ogc:Filter>","<ogc:Filter>", sld)
    sld = re.sub("</ogc:Filter>[ ]*?</ogc:Filter>","</ogc:Filter>", sld)
    if layer.hasScaleBasedVisibility():
        s = ("<MinScaleDenominator>" + str(layer.minimumScale()) +
        "</MinScaleDenominator><MaxScaleDenominator>" + str(layer.maximumScale()) + "</MaxScaleDenominator>")
        sld = sld.replace("<se:Rule>", "<se:Rule>" + s)
    sld = sld.replace("se:", "sld:")
    dasharrays = re.findall('<CssParameter name="stroke-dasharray">.*?</CssParameter>', sld)
    for arr in dasharrays:
        newpattern = " ".join([str(int(math.floor(float(i) * SIZE_FACTOR))) for i in arr[38:-15].strip().split(" ")])
        newdasharrays='<CssParameter name="stroke-dasharray">%s</CssParameter>' % newpattern
        sld = sld.replace(arr, newdasharrays)
    #//replace "native" SLD symbols
    wknReplacements = {}
    if layer.geometryType() == QgsWkbTypes.PointGeometry:
        wknReplacements = {"regular_star":"star",
                       "cross2": "x",
                       "equilateral_triangle": "triangle",
                       "rectangle": "square",
                       "filled_arrowhead": "ttf://Webdings#0x34",
                       "line": "shape://vertline",
                       "arrow": "ttf://Wingdings#0xE9",
                       "diamond": "ttf://Wingdings#0x75"}
    if layer.geometryType() == QgsWkbTypes.PolygonGeometry:
        wknReplacements = {"horline":"shape://horline",
                       "vertline":"shape://vertline",
                       "cross":"shape://plus",
                       "slash":"shape://slash",
                       "backslash":"shape://backslash",
                       "x": "shape://times"}
    for key,value in wknReplacements.items():
        sld = sld.replace("<sld:WellKnownName>%s</sld:WellKnownName>" % key,
                      "<sld:WellKnownName>%s</sld:WellKnownName>" % value)

    fontmarkers = re.findall('<sld:OnlineResource.*?"/> <sld:Format>ttf</sld:Format> <sld:MarkIndex>.*?</sld:MarkIndex>', sld)
    for arr in fontmarkers:
        police = re.findall('xlink:href=".*?"/>', arr)
        policeValue=police[0][12:-3]
        markerIndex = re.findall('<sld:MarkIndex>.*?</sld:MarkIndex>', arr)
        markerIndexValue=markerIndex[0][15:-16]
        sld = sld.replace(arr, '<WellKnownName>'+policeValue+'#'+hex(int(markerIndexValue))+'</WellKnownName>')
        
    icons = []
    renderer = layer.renderer()
    if isinstance(renderer, QgsSingleSymbolRenderer):
        icons = getReadyToUploadSvgIcons(renderer.symbol())
    elif isinstance(renderer, QgsCategorizedSymbolRenderer):
        for cat in renderer.categories():
            icons.extend(getReadyToUploadSvgIcons(cat.symbol()))
    elif isinstance(renderer, QgsGraduatedSymbolRenderer):
        for ran in renderer.ranges():
            icons.extend(getReadyToUploadSvgIcons(ran.symbol()))


    for icon in icons:
        for path in QgsApplication.svgPaths():
            path = os.path.normpath(path)
            if path[-1] != os.sep:
                path += os.sep
            relPath = os.path.normpath(icon[0]).replace(path, "").replace("\\", "/")
            sld = sld.replace(relPath, icon[1])

    return sld, icons

def resolveSvgPath(path):
    folders = QgsSettings().value('svg/searchPathsForSVG')
    for f in folders:
        fullPath = os.path.join(f, path)
        if os.path.exists(fullPath):
            return fullPath
    return None

def getReadyToUploadSvgIcons(symbol):
    icons = []
    for i in range(symbol.symbolLayerCount()):
        sl = symbol.symbolLayer(i)
        if isinstance(sl, QgsSvgMarkerSymbolLayer):
            path = resolveSvgPath(sl.path())
            if path is not None:
                props = sl.properties()
                with open(path) as f:
                    svg = "".join(f.readlines())
                svg = re.sub(r'param\(outline\).*?\"', props["outline_color"] + '"', svg)
                svg = re.sub(r'param\(fill\).*?\"', props["color"] + '"', svg)
                svg = re.sub(r'param\(outline-width\).*?\"', props["outline_width"] + '"', svg)
                basename = os.path.basename(sl.path())
                filename, ext = os.path.splitext(basename)
                propsHash = hash(frozenset(list(props.items())))
                icons.append ([sl.path(), "%s_%s%s" % (filename, propsHash, ext), svg])
        elif isinstance(sl, QgsSVGFillSymbolLayer):
            path = resolveSvgPath(sl.svgFilePath())
            if path is not None:
                props = sl.properties()
                with open(path) as f:
                    svg = "".join(f.readlines())
                svg = re.sub(r'param\(outline\).*?\"', props["outline_color"] + '"', svg)
                svg = re.sub(r'param\(fill\).*?\"', props["color"] + '"', svg)
                svg = re.sub(r'param\(outline-width\).*?\"', props["outline_width"] + '"', svg)
                basename = os.path.basename(sl.svgFilePath())
                filename, ext = os.path.splitext(basename)
                propsHash = hash(frozenset(list(props.items())))
                icons.append ([sl.svgFilePath(), "%s_%s%s" % (filename, propsHash, ext), svg])
            elif isinstance(sl, QgsMarkerLineSymbolLayer):
                return getReadyToUploadSvgIcons(sl.subSymbol())
    
    return icons

def adaptGsToQgs(sld):
    setScaleFactor()
    sizes = re.findall("<sld:Size>.*?</sld:Size>", sld)
    for size in sizes:
        newsize="<sld:Size>%f</sld:Size>" % (float(size[10:-11]) / SIZE_FACTOR)
        sld = sld.replace(size, newsize)
    widths = re.findall('<sld:CssParameter name="stroke-width">.*?</sld:CssParameter>', sld)
    for w in widths:
        newwidth='<CssParameter name="stroke-width">%f</CssParameter>' % (float(w[38:-19]) / SIZE_FACTOR)
        sld = sld.replace(w, newwidth)
    return sld

def getGsCompatibleSld(layer):
    sld = getStyleAsSld(layer)
    if sld is not None:
        return adaptQgsToGs(sld, layer)
    else:
        return None, None

def getStyleAsSld(layer):
    if layer.type() == layer.VectorLayer:
        document = QDomDocument()
        header = document.createProcessingInstruction( "xml", "version=\"1.0\" encoding=\"UTF-8\"" )
        document.appendChild( header )

        root = document.createElementNS( "http://www.opengis.net/sld", "StyledLayerDescriptor" )
        root.setAttribute( "version", "1.1.0" )
        root.setAttribute( "xsi:schemaLocation", "http://www.opengis.net/sld http://schemas.opengis.net/sld/1.1.0/StyledLayerDescriptor.xsd" )
        root.setAttribute( "xmlns:ogc", "http://www.opengis.net/ogc" )
        root.setAttribute( "xmlns:sld", "http://www.opengis.net/sld" )
        root.setAttribute( "xmlns:xlink", "http://www.w3.org/1999/xlink" )
        root.setAttribute( "xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance" )
        document.appendChild( root )

        namedLayerNode = document.createElement( "NamedLayer" )
        root.appendChild( namedLayerNode )

        errorMsg = ""
        layer.writeSld(namedLayerNode, document, errorMsg)
        return str(document.toString(4))
    elif layer.type() == layer.RasterLayer:
        renderer = layer.renderer()
        if isinstance(renderer, QgsSingleBandGrayRenderer):
            symbolizerCode = "<Opacity>%d</Opacity>" % renderer.opacity()
            symbolizerCode += ("<ChannelSelection><GrayChannel><SourceChannelName>"
                                + str(renderer.grayBand()) + "</SourceChannelName></GrayChannel></ChannelSelection>")
            sld =  RASTER_SLD_TEMPLATE.replace("SYMBOLIZER_CODE", symbolizerCode).replace("STYLE_NAME", layer.name())
            return sld
        elif isinstance(renderer, QgsSingleBandPseudoColorRenderer):
            symbolizerCode = "<ColorMap>"
            band = renderer.usesBands()[0]
            items = renderer.shader().rasterShaderFunction().colorRampItemList()
            for item in items:
                color = item.color
                rgb = '#%02x%02x%02x' % (color.red(), color.green(), color.blue())
                symbolizerCode += '<ColorMapEntry color="' + rgb + '" quantity="' + str(item.value) + '" />'
            symbolizerCode += "</ColorMap>"
            sld =  RASTER_SLD_TEMPLATE.replace("SYMBOLIZER_CODE", symbolizerCode).replace("STYLE_NAME", layer.name())
            return sld
        else:
            #we use some default styles in case we have an unsupported renderer
            sldpath = os.path.join(os.path.dirname(__file__), "..", "resources")
            if layer.bandCount() == 1:
                sldfile = os.path.join(sldpath, "grayscale.sld")
            else:
                sldfile = os.path.join(sldpath, "rgb.sld")
            with open(sldfile, 'r') as f:
                sld = f.read()
            return sld
    else:
        return None

def getGeomTypeFromSld(sld):
    if "PointSymbolizer" in sld:
        return "Point"
    elif "LineSymbolizer" in sld:
        return "LineString"
    else:
        return "Polygon"

def setUnits(layer):
    labeling = layer.labeling()
    if labeling is not None:
        settings = labeling.settings()
        settings.offsetUnits = QgsUnitTypes.RenderPixels
        labeling.setSettings(settings)
        layer.setLabeling(labeling)    