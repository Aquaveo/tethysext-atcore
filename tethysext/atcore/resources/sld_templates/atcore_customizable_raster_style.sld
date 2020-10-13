<?xml version="1.0" encoding="UTF-8"?>
<sld:StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:sld="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:gml="http://www.opengis.net/gml" version="1.0.0">
  <sld:NamedLayer>
    <sld:Name>atcore_customizable_raster_style</sld:Name>
    <sld:UserStyle>
      <sld:Name>atcore_customizable_raster_style</sld:Name>
      <sld:Title>ATCORE Customizable Raster Style</sld:Title>
      <sld:Abstract>Atcore's customizable raster style.</sld:Abstract>
      <sld:FeatureTypeStyle>
        <sld:Name>atcore_customizable_raster_style</sld:Name>
        <sld:Rule>
          <sld:RasterSymbolizer>
            <sld:ColorMap>
              <sld:ColorMapEntry color="${env('color0','#9EACFF')}" opacity="0" quantity="${env('val_no_data',0)}" label="nodata"/>
              <sld:ColorMapEntry color="${env('color1','#8F9BF5')}" quantity="${env('val1',0.1)}" label="Low"/>
              <sld:ColorMapEntry color="${env('color2','#808BEC')}" quantity="${env('val2',1)}"/>
              <sld:ColorMapEntry color="${env('color3','#717BE2')}" quantity="${env('val3',5)}"/>
              <sld:ColorMapEntry color="${env('color4','#636BD9')}" quantity="${env('val4',10)}"/>
              <sld:ColorMapEntry color="${env('color5','#545BCF')}" quantity="${env('val5',25)}"/>
              <sld:ColorMapEntry color="${env('color6','#454BC6')}" quantity="${env('val6',50)}"/>
              <sld:ColorMapEntry color="${env('color7','#373BBC')}" quantity="${env('val7',100)}"/>
              <sld:ColorMapEntry color="${env('color8','#282BB3')}" quantity="${env('val8',200)}"/>
              <sld:ColorMapEntry color="${env('color9','#191BA9')}" quantity="${env('val9',500)}"/>
              <sld:ColorMapEntry color="${env('color10','#0B0BA0')}" quantity="${env('val10',1000)}"  label="High"/>
            </sld:ColorMap>
            <sld:ContrastEnhancement/>
          </sld:RasterSymbolizer>
        </sld:Rule>
      </sld:FeatureTypeStyle>
    </sld:UserStyle>
  </sld:NamedLayer>
</sld:StyledLayerDescriptor>
