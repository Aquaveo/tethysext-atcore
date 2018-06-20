<?xml version="1.0" encoding="ISO-8859-1"?>
<StyledLayerDescriptor
  version="1.0.0"
  xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd"
  xmlns="http://www.opengis.net/sld"
  xmlns:ogc="http://www.opengis.net/ogc"
  xmlns:xlink="http://www.w3.org/1999/xlink"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <!-- a Named Layer is the basic building block of an SLD document -->
  <NamedLayer>
    <Name>Zones</Name>
    <UserStyle>
      <!-- Styles can have names, titles and abstracts -->
      <Title>Zones</Title>
      <Abstract>A generic color map to an EPANET report node layer with a property called "{{ variable }}"</Abstract>
      <!-- FeatureTypeStyles describe how to render different features -->
      <!-- A FeatureTypeStyle for rendering points -->
      <FeatureTypeStyle>
        {# BOUNDARY ZONES #}
        {% if feature_type == 'links' %}
        <Rule>
          <Title>Zone Boundaries</Title>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">{{ boundary_zone_color }}</CssParameter>
              <CssParameter name="stroke-width">2</CssParameter>
            </Stroke>
          </LineSymbolizer>
        </Rule>
        {% endif %}

        {# NORMAL ZONES #}
        {% for zone_color in zone_ramp %}
          {% if feature_type == 'links' %}
          <Rule>
            <Title>Zone {{ loop.index }}</Title>
            <ogc:Filter>
              <ogc:And>
                <ogc:PropertyIsEqualTo>
                  <ogc:PropertyName>zone_name</ogc:PropertyName>
                  <ogc:Literal>N{{ loop.index - 1}}</ogc:Literal>
                </ogc:PropertyIsEqualTo>
                <ogc:PropertyIsEqualTo>
                  <ogc:PropertyName>type</ogc:PropertyName>
                  <ogc:Literal>PIPE</ogc:Literal>
                </ogc:PropertyIsEqualTo>
              </ogc:And>
            </ogc:Filter>
            <LineSymbolizer>
              <Stroke>
                <CssParameter name="stroke">{{ zone_color }}</CssParameter>
                <CssParameter name="stroke-width">2</CssParameter>
              </Stroke>
            </LineSymbolizer>
          </Rule>
          <Rule>
            <Title>Zone {{ loop.index }}</Title>
            <ogc:Filter>
              <ogc:And>
                <ogc:PropertyIsEqualTo>
                  <ogc:PropertyName>zone_name</ogc:PropertyName>
                  <ogc:Literal>N{{ loop.index - 1}}</ogc:Literal>
                </ogc:PropertyIsEqualTo>
                <ogc:PropertyIsEqualTo>
                  <ogc:PropertyName>type</ogc:PropertyName>
                  <ogc:Literal>VALVE</ogc:Literal>
                </ogc:PropertyIsEqualTo>
              </ogc:And>
            </ogc:Filter>
            <LineSymbolizer>
              <Stroke>
                <CssParameter name="stroke">{{ zone_color }}</CssParameter>
                <CssParameter name="stroke-width">2</CssParameter>
              </Stroke>
            </LineSymbolizer>
            <PointSymbolizer>
              <Graphic>
                <ExternalGraphic>
                  <OnlineResource
                    xmlns:xlink="http://www.w3.org/1999/xlink"
                    xlink:type="simple"
                    xlink:href="{{ valve_image_url }}"/>
                  <Format>image/png</Format>
                </ExternalGraphic>
                <Size>18</Size>
              </Graphic>
            </PointSymbolizer>
          </Rule>
          <Rule>
            <Title>Zone {{ loop.index }}</Title>
            <ogc:Filter>
              <ogc:And>
                <ogc:PropertyIsEqualTo>
                  <ogc:PropertyName>zone_name</ogc:PropertyName>
                  <ogc:Literal>N{{ loop.index - 1}}</ogc:Literal>
                </ogc:PropertyIsEqualTo>
                <ogc:PropertyIsEqualTo>
                  <ogc:PropertyName>type</ogc:PropertyName>
                  <ogc:Literal>PUMP</ogc:Literal>
                </ogc:PropertyIsEqualTo>
              </ogc:And>
            </ogc:Filter>
            <LineSymbolizer>
              <Stroke>
                <CssParameter name="stroke">{{ zone_color }}</CssParameter>
                <CssParameter name="stroke-width">2</CssParameter>
              </Stroke>
            </LineSymbolizer>
            <PointSymbolizer>
              <Graphic>
                <ExternalGraphic>
                  <OnlineResource
                    xmlns:xlink="http://www.w3.org/1999/xlink"
                    xlink:type="simple"
                    xlink:href="{{ pump_image_url }}"/>
                  <Format>image/png</Format>
                </ExternalGraphic>
                <Size>18</Size>
              </Graphic>
            </PointSymbolizer>
          </Rule>
          {% else %}
          <Rule>
            <Title>Zone {{ loop.index }}</Title>
            <ogc:Filter>
              <ogc:And>
                <ogc:PropertyIsEqualTo>
                  <ogc:PropertyName>zone_name</ogc:PropertyName>
                  <ogc:Literal>N{{ loop.index - 1}}</ogc:Literal>
                </ogc:PropertyIsEqualTo>
                <ogc:PropertyIsEqualTo>
                  <ogc:PropertyName>type</ogc:PropertyName>
                  <ogc:Literal>JUNCTION</ogc:Literal>
                </ogc:PropertyIsEqualTo>
              </ogc:And>
            </ogc:Filter>
            <PointSymbolizer>
              <Graphic>
                <Mark>
                  <WellKnownName>circle</WellKnownName>
                  <Fill>
                    <CssParameter name="fill">{{ zone_color }}</CssParameter>
                  </Fill>
                </Mark>
                <Size>6</Size>
              </Graphic>
            </PointSymbolizer>
          </Rule>
          <Rule>
            <Title>Zone {{ loop.index }}</Title>
            <ogc:Filter>
              <ogc:And>
                <ogc:PropertyIsEqualTo>
                  <ogc:PropertyName>zone_name</ogc:PropertyName>
                  <ogc:Literal>N{{ loop.index - 1}}</ogc:Literal>
                </ogc:PropertyIsEqualTo>
                <ogc:PropertyIsEqualTo>
                  <ogc:PropertyName>type</ogc:PropertyName>
                  <ogc:Literal>TANK</ogc:Literal>
                </ogc:PropertyIsEqualTo>
              </ogc:And>
            </ogc:Filter>
            <PointSymbolizer>
              <Graphic>
                <Mark>
                  <WellKnownName>square</WellKnownName>
                  <Fill>
                    <CssParameter name="fill">{{ zone_color }}</CssParameter>
                  </Fill>
                  <Stroke>
                    <CssParameter name="stroke">#FFFFFF</CssParameter>
                  </Stroke>
                </Mark>
                <Size>15</Size>
              </Graphic>
            </PointSymbolizer>
          </Rule>
          <Rule>
            <Title>Zone {{ loop.index }}</Title>
            <ogc:Filter>
              <ogc:And>
                <ogc:PropertyIsEqualTo>
                  <ogc:PropertyName>zone_name</ogc:PropertyName>
                  <ogc:Literal>N{{ loop.index - 1}}</ogc:Literal>
                </ogc:PropertyIsEqualTo>
                <ogc:PropertyIsEqualTo>
                  <ogc:PropertyName>type</ogc:PropertyName>
                  <ogc:Literal>RESERVOIR</ogc:Literal>
                </ogc:PropertyIsEqualTo>
              </ogc:And>
            </ogc:Filter>
            <PointSymbolizer>
              <Graphic>
                <Mark>
                  <WellKnownName>triangle</WellKnownName>
                  <Fill>
                    <CssParameter name="fill">{{ zone_color }}</CssParameter>
                  </Fill>
                  <Stroke>
                  <CssParameter name="stroke">#FFFFFF</CssParameter>
                </Stroke>
                </Mark>
                <Size>15</Size>
              </Graphic>
            </PointSymbolizer>
          </Rule>
          {% endif %}
        {% endfor %}
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>