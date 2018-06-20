<?xml version="1.0" encoding="ISO-8859-1"?>
<StyledLayerDescriptor
  version="1.0.0"
  xmlns="http://www.opengis.net/sld"
  xmlns:ogc="http://www.opengis.net/ogc"
  xmlns:xlink="http://www.w3.org/1999/xlink"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd">
  <!-- a Named Layer is the basic building block of an SLD document -->
  <NamedLayer>
    <Name>{{ variable|title }} Link</Name>
    <UserStyle>
      <!-- Styles can have names, titles and abstracts -->
      <Title>{{ variable|title }} Link</Title>
      <Abstract>A generic color map to an EPANET report link layer with a property called {{ variable }}"</Abstract>
      <!-- FeatureTypeStyles describe how to render different features -->
      <!-- A FeatureTypeStyle for rendering points -->
      <FeatureTypeStyle>
        <Rule>
          <Title>{{ variable|title }} Division 1</Title>
          <ogc:Filter>
            <ogc:PropertyIsLessThan>
              <ogc:PropertyName>{{ variable }}</ogc:PropertyName>
              <ogc:Function name="env">
                <ogc:Literal>division1</ogc:Literal>
                <ogc:Literal>{{ division1 }}</ogc:Literal>
              </ogc:Function>
            </ogc:PropertyIsLessThan>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">
                <ogc:Function name="env">
                  <ogc:Literal>color1</ogc:Literal>
                  <ogc:Literal>{{ color1|default('#0000FF') }}</ogc:Literal>
                </ogc:Function>
              </CssParameter>
              <CssParameter name="stroke-width">2</CssParameter>
            </Stroke>
          </LineSymbolizer>
          {% if is_label_style %}
          <TextSymbolizer>
            <Label>
              <PropertyName>{{ variable }}</PropertyName>
            </Label>
            <Font>
              <CssParameter name="font-size">12</CssParameter>
            </Font>
            <LabelPlacement>
              <LinePlacement>
                <PerpendicularOffset>10</PerpendicularOffset>
              </LinePlacement>
            </LabelPlacement>
            <Halo>
              <Radius>3</Radius>
              <Fill>
                <CssParameter name="fill-opacity">0.9</CssParameter>
              </Fill>
            </Halo>
          </TextSymbolizer>
          {% endif %}
        </Rule>
        <Rule>
          <Title>{{ variable|title }} Division 2</Title>
          <ogc:Filter>
            <ogc:PropertyIsBetween>
              <ogc:PropertyName>{{ variable }}</ogc:PropertyName>
              <ogc:LowerBoundary>
                <ogc:Function name="env">
                  <ogc:Literal>division1</ogc:Literal>
                  <ogc:Literal>{{ division1 }}</ogc:Literal>
                </ogc:Function>
              </ogc:LowerBoundary>
              <ogc:UpperBoundary>
                <ogc:Function name="env">
                  <ogc:Literal>division2</ogc:Literal>
                  <ogc:Literal>{{ division2 }}</ogc:Literal>
                </ogc:Function>
              </ogc:UpperBoundary>
            </ogc:PropertyIsBetween>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">
                <ogc:Function name="env">
                  <ogc:Literal>color2</ogc:Literal>
                  <ogc:Literal>{{ color2|default('#00FFFF') }}</ogc:Literal>
                </ogc:Function>
              </CssParameter>
              <CssParameter name="stroke-width">2</CssParameter>
            </Stroke>
          </LineSymbolizer>
          {% if is_label_style %}
          <TextSymbolizer>
            <Label>
              <PropertyName>{{ variable }}</PropertyName>
            </Label>
            <Font>
              <CssParameter name="font-size">12</CssParameter>
            </Font>
            <LabelPlacement>
              <LinePlacement>
                <PerpendicularOffset>10</PerpendicularOffset>
              </LinePlacement>
            </LabelPlacement>
            <Halo>
              <Radius>3</Radius>
              <Fill>
                <CssParameter name="fill-opacity">0.9</CssParameter>
              </Fill>
            </Halo>
          </TextSymbolizer>
          {% endif %}
        </Rule>
        <Rule>
          <Title>{{ variable|title }} Division 3</Title>
          <ogc:Filter>
            <ogc:PropertyIsBetween>
              <ogc:PropertyName>{{ variable }}</ogc:PropertyName>
              <ogc:LowerBoundary>
                <ogc:Function name="env">
                  <ogc:Literal>division2</ogc:Literal>
                  <ogc:Literal>{{ division2 }}</ogc:Literal>
                </ogc:Function>
              </ogc:LowerBoundary>
              <ogc:UpperBoundary>
                <ogc:Function name="env">
                  <ogc:Literal>division3</ogc:Literal>
                  <ogc:Literal>{{ division3 }}</ogc:Literal>
                </ogc:Function>
              </ogc:UpperBoundary>
            </ogc:PropertyIsBetween>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">
                <ogc:Function name="env">
                  <ogc:Literal>color3</ogc:Literal>
                  <ogc:Literal>{{ color3|default('#00FF00') }}</ogc:Literal>
                </ogc:Function>
              </CssParameter>
              <CssParameter name="stroke-width">2</CssParameter>
            </Stroke>
          </LineSymbolizer>
          {% if is_label_style %}
          <TextSymbolizer>
            <Label>
              <PropertyName>{{ variable }}</PropertyName>
            </Label>
            <Font>
              <CssParameter name="font-size">12</CssParameter>
            </Font>
            <LabelPlacement>
              <LinePlacement>
                <PerpendicularOffset>10</PerpendicularOffset>
              </LinePlacement>
            </LabelPlacement>
            <Halo>
              <Radius>3</Radius>
              <Fill>
                <CssParameter name="fill-opacity">0.9</CssParameter>
              </Fill>
            </Halo>
          </TextSymbolizer>
          {% endif %}
        </Rule>
        <Rule>
          <Title>{{ variable|title }} Division 4</Title>
          <ogc:Filter>
            <ogc:PropertyIsBetween>
              <ogc:PropertyName>{{ variable }}</ogc:PropertyName>
              <ogc:LowerBoundary>
                <ogc:Function name="env">
                  <ogc:Literal>division3</ogc:Literal>
                  <ogc:Literal>{{ division3 }}</ogc:Literal>
                </ogc:Function>
              </ogc:LowerBoundary>
              <ogc:UpperBoundary>
                <ogc:Function name="env">
                  <ogc:Literal>division4</ogc:Literal>
                  <ogc:Literal>{{ division4 }}</ogc:Literal>
                </ogc:Function>
              </ogc:UpperBoundary>
            </ogc:PropertyIsBetween>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">
                <ogc:Function name="env">
                  <ogc:Literal>color4</ogc:Literal>
                  <ogc:Literal>{{ color4|default('#FFFF00') }}</ogc:Literal>
                </ogc:Function>
              </CssParameter>
              <CssParameter name="stroke-width">2</CssParameter>
            </Stroke>
          </LineSymbolizer>
          {% if is_label_style %}
          <TextSymbolizer>
            <Label>
              <PropertyName>{{ variable }}</PropertyName>
            </Label>
            <Font>
              <CssParameter name="font-size">12</CssParameter>
            </Font>
            <LabelPlacement>
              <LinePlacement>
                <PerpendicularOffset>10</PerpendicularOffset>
              </LinePlacement>
            </LabelPlacement>
            <Halo>
              <Radius>3</Radius>
              <Fill>
                <CssParameter name="fill-opacity">0.9</CssParameter>
              </Fill>
            </Halo>
          </TextSymbolizer>
          {% endif %}
        </Rule>
        <Rule>
          <Title>{{ variable|title }} Division 5</Title>
          <ogc:Filter>
            <ogc:PropertyIsGreaterThan>
              <ogc:PropertyName>{{ variable }}</ogc:PropertyName>
              <ogc:Function name="env">
                <ogc:Literal>division4</ogc:Literal>
                <ogc:Literal>{{ division4 }}</ogc:Literal>
              </ogc:Function>
            </ogc:PropertyIsGreaterThan>
          </ogc:Filter>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">
                <ogc:Function name="env">
                  <ogc:Literal>color5</ogc:Literal>
                  <ogc:Literal>{{ color5|default('#FF0000') }}</ogc:Literal>
                </ogc:Function>
              </CssParameter>
              <CssParameter name="stroke-width">2</CssParameter>
            </Stroke>
          </LineSymbolizer>
          {% if is_label_style %}
          <TextSymbolizer>
            <Label>
              <PropertyName>{{ variable }}</PropertyName>
            </Label>
            <Font>
              <CssParameter name="font-size">12</CssParameter>
            </Font>
            <LabelPlacement>
              <LinePlacement>
                <PerpendicularOffset>10</PerpendicularOffset>
              </LinePlacement>
            </LabelPlacement>
            <Halo>
              <Radius>3</Radius>
              <Fill>
                <CssParameter name="fill-opacity">0.9</CssParameter>
              </Fill>
            </Halo>
          </TextSymbolizer>
          {% endif %}
        </Rule>
        <Rule>
          <Title>Pumps</Title>
          <ogc:Filter>
            <ogc:PropertyIsEqualTo>
              <ogc:PropertyName>type</ogc:PropertyName>
              <ogc:Literal>PUMP</ogc:Literal>
            </ogc:PropertyIsEqualTo>
          </ogc:Filter>
          <PointSymbolizer>
            <Graphic>
              <ExternalGraphic>
                <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink"
                                xlink:type="simple"
                                xlink:href="{{ pump_image_url }}"/>
                <Format>image/png</Format>
              </ExternalGraphic>
              <Size>18</Size>
            </Graphic>
          </PointSymbolizer>
        </Rule>
        <Rule>
          <Title>Valves</Title>
          <ogc:Filter>
            <ogc:PropertyIsEqualTo>
              <ogc:PropertyName>type</ogc:PropertyName>
              <ogc:Literal>VALVE</ogc:Literal>
            </ogc:PropertyIsEqualTo>
          </ogc:Filter>
          <PointSymbolizer>
            <Graphic>
              <ExternalGraphic>
                <OnlineResource xmlns:xlink="http://www.w3.org/1999/xlink"
                                xlink:type="simple"
                                xlink:href="{{ valve_image_url }}"/>
                <Format>image/png</Format>
              </ExternalGraphic>
              <Size>18</Size>
            </Graphic>
          </PointSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>