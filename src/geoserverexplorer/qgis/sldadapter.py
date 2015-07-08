'''
methods to convert the SLD produced by GeoServer (1.0) to the SLD produced by QGIS (1.1), and also the other way round.
This is a quick and dirty solution until both programs support the same specification
'''

import re
import os
from PyQt4.QtXml import *
from qgis.core import *

SIZE_FACTOR = 4
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

def adaptQgsToGs(sld, layer):

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
    labeling = layer.customProperty("labeling/enabled")
    labeling = str(labeling).lower() == str(True).lower()
    if labeling:
        s = getLabelingAsSld(layer)
        sld = sld.replace("<se:Rule>", "<se:Rule>" + s)
    sld = sld.replace("se:", "sld:")
    sizes = re.findall("<sld:Size>.*?</sld:Size>", sld)
    for size in sizes:
        newsize="<sld:Size>%f</sld:Size>" % (float(size[10:-11]) * SIZE_FACTOR)
        sld = sld.replace(size, newsize)
    widths = re.findall('<CssParameter name="stroke-width">.*?</CssParameter>', sld)
    for w in widths:
        newwidth='<CssParameter name="stroke-width">%f</CssParameter>' % (float(w[34:-15]) * SIZE_FACTOR)
        sld = sld.replace(w, newwidth)
    #//replace "native" SLD symbols
    wknReplacements = {}
    if layer.geometryType() == QGis.Point:
        wknReplacements = {"regular_star":"star",
                       "cross2": "x",
                       "equilateral_triangle": "triangle",
                       "rectangle": "square",
                       "filled_arrowhead": "ttf://Webdings#0x34",
                       "line": "shape://vertline",
                       "arrow": "ttf:Webdings#0x7F18",
                       "diamond": "ttf://Wingdings#0x75"}
    if layer.geometryType() == QGis.Polygon:
        wknReplacements = {"horline":"shape://horline",
                       "vertline":"shape://vertline",
                       "cross":"shape://plus",
                       "slash":"shape://slash",
                       "backslash":"shape://backslash",
                       "x": "shape://times"}
    for key,value in wknReplacements.iteritems():
        sld = sld.replace("<sld:WellKnownName>%s</sld:WellKnownName>" % key,
                      "<sld:WellKnownName>%s</sld:WellKnownName>" % value)


    icons = []
    renderer = layer.rendererV2()
    if isinstance(renderer, QgsSingleSymbolRendererV2):
        icons = getReadyToUploadSvgIcons(renderer.symbol())
    elif isinstance(renderer, QgsCategorizedSymbolRendererV2):
        for cat in renderer.categories():
            icons.extend(getReadyToUploadSvgIcons(cat.symbol()))
    elif isinstance(renderer, QgsGraduatedSymbolRendererV2):
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

def getReadyToUploadSvgIcons(symbol):
    icons = []
    for i in xrange(symbol.symbolLayerCount()):
        sl = symbol.symbolLayer(i)
        if isinstance(sl, QgsSvgMarkerSymbolLayerV2):
            props = sl.properties()
            with open(sl.path()) as f:
                svg = "".join(f.readlines())
            svg = re.sub(r'param\(outline\).*?\"', props["outline_color"] + '"', svg)
            svg = re.sub(r'param\(fill\).*?\"', props["color"] + '"', svg)
            svg = re.sub(r'param\(outline-width\).*?\"', props["outline_width"] + '"', svg)
            basename = os.path.basename(sl.path())
            filename, ext = os.path.splitext(basename)
            propsHash = hash(frozenset(props.items()))
            icons.append ([sl.path(), "%s_%s%s" % (filename, propsHash, ext), svg])
        elif isinstance(sl, QgsSVGFillSymbolLayer):
            props = sl.properties()
            with open(sl.svgFilePath()) as f:
                svg = "".join(f.readlines())
            svg = re.sub(r'param\(outline\).*?\"', props["outline_color"] + '"', svg)
            svg = re.sub(r'param\(fill\).*?\"', props["color"] + '"', svg)
            svg = re.sub(r'param\(outline-width\).*?\"', props["outline_width"] + '"', svg)
            basename = os.path.basename(sl.svgFilePath())
            filename, ext = os.path.splitext(basename)
            propsHash = hash(frozenset(props.items()))
            icons.append ([sl.svgFilePath(), "%s_%s%s" % (filename, propsHash, ext), svg])
        elif isinstance(sl, QgsMarkerLineSymbolLayerV2):
            return getReadyToUploadSvgIcons(sl.subSymbol())
    return icons

def getLabelingAsSld(layer):
    try:
        s = "<TextSymbolizer><Label>"
        s += "<ogc:PropertyName>" + layer.customProperty("labeling/fieldName") + "</ogc:PropertyName>"
        s += "</Label>"
        r = int(layer.customProperty("labeling/textColorR"))
        g = int(layer.customProperty("labeling/textColorG"))
        b = int(layer.customProperty("labeling/textColorB"))
        rgb = '#%02x%02x%02x' % (r, g, b)
        s += '<Fill><CssParameter name="fill">' + rgb + "</CssParameter></Fill>"
        s += "<Font>"
        s += '<CssParameter name="font-family">' + layer.customProperty("labeling/fontFamily") +'</CssParameter>'
        s += ('<CssParameter name="font-size">' +
                str(float(layer.customProperty("labeling/fontSize")) * SIZE_FACTOR)
                +'</CssParameter>')
        if layer.customProperty("labeling/fontItalic") == "true":
            s += '<CssParameter name="font-style">italic</CssParameter>'
        if layer.customProperty("labeling/fontBold") == "true":
            s += '<CssParameter name="font-weight">bold</CssParameter>'
        s += "</Font>"
        s += "<LabelPlacement>"
        if layer.geometryType() == QGis.Point:
            s += ("<PointPlacement>"
                "<AnchorPoint>"
                "<AnchorPointX>0.5</AnchorPointX>"
                "<AnchorPointY>0.5</AnchorPointY>"
                "</AnchorPoint>")
            s += "<Displacement>"
            s += "<DisplacementX>" + str(layer.customProperty("labeling/xOffset")) + "</DisplacementX>"
            s += "<DisplacementY>" + str(layer.customProperty("labeling/yOffset")) + "</DisplacementY>"
            s += "</Displacement>"
            s += "<Rotation>-" + str(layer.customProperty("labeling/angleOffset")) + "</Rotation>"
            s += "</PointPlacement>"
        elif layer.geometryType() == QGis.Line:
            mode = layer.customProperty("labeling/placement")
            print mode
            if mode != 4:
                follow = '<VendorOption name="followLine">true</VendorOption>' if mode == 3 else ''
                s += '''<LinePlacement>
                        <PerpendicularOffset>
                           %s
                        </PerpendicularOffset>
                      </LinePlacement>
                      %s''' %  (str(layer.customProperty("labeling/dist")), follow)
        s += "</LabelPlacement>"

        if layer.customProperty("labeling/bufferDraw") == "true":
            r = int(layer.customProperty("labeling/bufferColorR"))
            g = int(layer.customProperty("labeling/bufferColorG"))
            b = int(layer.customProperty("labeling/bufferColorB"))
            rgb = '#%02x%02x%02x' % (r, g, b)
            haloSize = str(layer.customProperty("labeling/bufferSize"))
            opacity = str(float(layer.customProperty("labeling/bufferColorA")) / 255.0)
            s += "<Halo><Radius>%s</Radius><Fill>" % haloSize
            s +=  '<CssParameter name="fill">%s</CssParameter>' % rgb
            s += '<CssParameter name="fill-opacity">%s</CssParameter></Fill></Halo>' % opacity
        s +="</TextSymbolizer>"
        return s
    except:
        return ""

def adaptGsToQgs(sld):
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

        return unicode(document.toString(4))
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
                symbolizerCode += '<ColorMapEntry color="' + rgb + '" quantity="' + unicode(item.value) + '" />'
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
