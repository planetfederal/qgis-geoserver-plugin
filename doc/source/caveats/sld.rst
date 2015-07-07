This document describes the symbology elements from QGIS that are supported when publishing a QGIS layer to GeoServer using the OpenGeo Suite plugin. Layers with symbologies using these elements are guaranteed to have the same styling once published to GeoServer. Otherwise, differences must be found.

General
========

All units have to be in milimeters.

Data defined properties are not supported for any type of symbology or element.

Layer transparency is supported, but layer blending is not.

SVG icons are supported as long as the symbology only uses one version of the icon in terms of color properties. That is, if the symbology uses the SVG plane icon, it is not possible to have a categorized symbology in which one of the categories uses the icon with a red color and another one where it is used with a blue color. This is due to the fact that QGIS support parameters in SVG files, while GeoServer does not.

Point layers
============

Supported symbology types: Single Symbol, Categorized, Graduated

Supported symbol layer types:

	# Simple marker: All properties of markers are supported except Angle, Offset and Anchor point.

	All simple marker shapes are supported except pentagon

	# SVG markers.  All properties of SVG markers are supported except Angle, Offset and Anchor point.

Multi-layered symbols can be used, as long as the same SVG icon is not used with different properties in different symbol layers, as described in the General section.



Line layers
============

Supported symbology types: Single Symbol, Categorized, Graduated

Supported symbol layer types:

	# Simple line: All properties of markers are supported except custom dash pattern

	# Marker line. Supported, but parameters are not used. Only marker definition itself is used.

Multi-layered symbols can be used, as long as the same SVG icon is not used with different properties in different symbol layers, as described in the General section.


Polygon layers
===============

Supported symbology types: Single Symbol, Categorized, Graduated

Supported symbol layer types:

	# Simple fill: All properties are supported

	# Line pattern fill: Only the Distance parameter is supported. The lines that define the pattern must be single-layered and the layer type must be "Simple line"

	# SVGFill: All parameters are supported except Rotation

Multi-layered symbols can be used, as long as the same SVG icon is not used with different properties in different symbol layers, as described in the General section.


Labelling
============

Only parameters in the Text and Placement sections are supported.

Text section
--------------

Supported parameters: Style, Size, Color. Size only supported in points

Placement section
------------------

Supported parameters: Displacement, Rotation (in "Offset from point" option)



