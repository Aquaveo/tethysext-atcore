<?xml version="1.0" encoding="ISO-8859-1"?>
<StyledLayerDescriptor version="1.0.0"
 xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd"
 xmlns="http://www.opengis.net/sld"
 xmlns:ogc="http://www.opengis.net/ogc"
 xmlns:xlink="http://www.w3.org/1999/xlink"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <!-- a Named Layer is the basic building block of an SLD document -->
  <NamedLayer>
    <Name>resource_extent_layer</Name>
    <UserStyle>
    <!-- Styles can have names, titles and abstracts -->
      <Title>Resource Extent</Title>
      <Abstract>Extent of a Resource</Abstract>
      <!-- FeatureTypeStyles describe how to render different features -->
      <!-- A FeatureTypeStyle for rendering polygons -->
      <FeatureTypeStyle>
        <Rule>
          <Name>rule1</Name>
          <Title>Resource Extent</Title>
          <Abstract>Extent of a resource</Abstract>
          <PolygonSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#FFD400</CssParameter>
              <CssParameter name="stroke-width">3</CssParameter>
            </Stroke>
          </PolygonSymbolizer>
          <PointSymbolizer>
            <Graphic>
             <Mark>
               <WellKnownName>circle</WellKnownName>
               <Fill>
                 <CssParameter name="fill">#FFD400</CssParameter>
               </Fill>
             </Mark>
             <Size>6</Size>
            </Graphic>
          </PointSymbolizer>
          <LineSymbolizer>
            <Stroke>
             <CssParameter name="stroke">#FFD400</CssParameter>
             <CssParameter name="stroke-width">3</CssParameter>
             <CssParameter name="stroke-dasharray">5 2</CssParameter>
            </Stroke>
          </LineSymbolizer>
          {% if is_label_style %}
          <TextSymbolizer>
            <Label>
              <PropertyName>{{ label_property }}</PropertyName>
              <ogc:Function name="env">
                <ogc:Literal>units</ogc:Literal>
                <ogc:Literal> sq-km</ogc:Literal>
              </ogc:Function>
            </Label>
            <Font>
              <CssParameter name="font-size">12</CssParameter>
            </Font>
            <Halo>
              <Radius>3</Radius>
              <Fill>
                <CssParameter name="fill-opacity">0.9</CssParameter>
                <CssParameter name="fill">#FFFFFF</CssParameter>
              </Fill>
            </Halo>
          </TextSymbolizer>
          {% endif %}
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>
