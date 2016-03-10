<?xml version="1.0" encoding="UTF-8"?>
<sld:StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:sld="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:gml="http://www.opengis.net/gml" version="1.0.0">
  <sld:NamedLayer>
    <sld:Name>grayscale_raster</sld:Name>
    <sld:UserStyle>
      <sld:Name>Grayscale raster</sld:Name>
      <sld:Title/>
      <sld:FeatureTypeStyle>
        <sld:Name>name</sld:Name>
        <sld:Rule>
          <sld:Name>Single symbol</sld:Name>
          <RasterSymbolizer>
            <Opacity>1.0</Opacity>
            <ChannelSelection>
                <GrayChannel>
                  <SourceChannelName>1</SourceChannelName>
                </GrayChannel>
            </ChannelSelection>        
          </RasterSymbolizer>
        </sld:Rule>
      </sld:FeatureTypeStyle>
    </sld:UserStyle>
  </sld:NamedLayer>
</sld:StyledLayerDescriptor>