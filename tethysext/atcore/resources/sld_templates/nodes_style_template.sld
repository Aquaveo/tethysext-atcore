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
    <Name>{{ variable|title }} Report</Name>
    <UserStyle>
      <!-- Styles can have names, titles and abstracts -->
      <Title>{{ variable|title }} Report</Title>
      <Abstract>A generic color map to an EPANET report node layer with a property called "{{ variable }}"</Abstract>
      <!-- FeatureTypeStyles describe how to render different features -->
      <!-- A FeatureTypeStyle for rendering points -->
      <FeatureTypeStyle>
        <Rule>
          <Title>Junctions Division 1</Title>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsLessThan>
                <ogc:PropertyName>{{ variable }}</ogc:PropertyName>
                <ogc:Function name="env">
                  <ogc:Literal>division1</ogc:Literal>
                  <ogc:Literal>{{ division1 }}</ogc:Literal>
                </ogc:Function>
              </ogc:PropertyIsLessThan>
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
                  <CssParameter name="fill">
                    <ogc:Function name="env">
                      <ogc:Literal>color1</ogc:Literal>
                      <ogc:Literal>{{ color1|default('#0000FF') }}</ogc:Literal>
                    </ogc:Function>
                  </CssParameter>
                </Fill>
              </Mark>
              <Size>6</Size>
            </Graphic>
          </PointSymbolizer>
          {% if is_label_style %}
          <TextSymbolizer>
            <Label>
              <PropertyName>{{ variable }}</PropertyName>
            </Label>
            <Font>
              <CssParameter name="font-size">12</CssParameter>
            </Font>
            <LabelPlacement>
              <PointPlacement>
                <AnchorPoint>
                  <AnchorPointX>0.5</AnchorPointX>
                  <AnchorPointY>0.0</AnchorPointY>
                </AnchorPoint>
                <Displacement>
                  <DisplacementX>0</DisplacementX>
                  <DisplacementY>5</DisplacementY>
                </Displacement>
              </PointPlacement>
            </LabelPlacement>
            <Halo>
              <Radius>3</Radius>
              <Fill>
                <CssParameter name="fill-opacity">0.9</CssParameter>
              </Fill>
            </Halo>
          </TextSymbolizer>
          {% endif %}
          {% if is_label_style %}
          <TextSymbolizer>
            <Label>
              <PropertyName>{{ variable }}</PropertyName>
            </Label>
            <Font>
              <CssParameter name="font-size">12</CssParameter>
            </Font>
            <LabelPlacement>
              <PointPlacement>
                <AnchorPoint>
                  <AnchorPointX>0.5</AnchorPointX>
                  <AnchorPointY>0.0</AnchorPointY>
                </AnchorPoint>
                <Displacement>
                  <DisplacementX>0</DisplacementX>
                  <DisplacementY>5</DisplacementY>
                </Displacement>
              </PointPlacement>
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
          <Title>Junctions Division 2</Title>
          <ogc:Filter>
            <ogc:And>
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
                  <CssParameter name="fill">
                    <ogc:Function name="env">
                      <ogc:Literal>color2</ogc:Literal>
                      <ogc:Literal>{{ color2|default('#00FFFF') }}</ogc:Literal>
                    </ogc:Function>
                  </CssParameter>
                </Fill>
              </Mark>
              <Size>6</Size>
            </Graphic>
          </PointSymbolizer>
          {% if is_label_style %}
          <TextSymbolizer>
            <Label>
              <PropertyName>{{ variable }}</PropertyName>
            </Label>
            <Font>
              <CssParameter name="font-size">12</CssParameter>
            </Font>
            <LabelPlacement>
              <PointPlacement>
                <AnchorPoint>
                  <AnchorPointX>0.5</AnchorPointX>
                  <AnchorPointY>0.0</AnchorPointY>
                </AnchorPoint>
                <Displacement>
                  <DisplacementX>0</DisplacementX>
                  <DisplacementY>5</DisplacementY>
                </Displacement>
              </PointPlacement>
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
          <Title>Junctions Division 3</Title>
          <ogc:Filter>
            <ogc:And>
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
                  <CssParameter name="fill">
                    <ogc:Function name="env">
                      <ogc:Literal>color3</ogc:Literal>
                      <ogc:Literal>{{ color3|default('#00FF00') }}</ogc:Literal>
                    </ogc:Function>
                  </CssParameter>
                </Fill>
              </Mark>
              <Size>6</Size>
            </Graphic>
          </PointSymbolizer>
          {% if is_label_style %}
          <TextSymbolizer>
            <Label>
              <PropertyName>{{ variable }}</PropertyName>
            </Label>
            <Font>
              <CssParameter name="font-size">12</CssParameter>
            </Font>
            <LabelPlacement>
              <PointPlacement>
                <AnchorPoint>
                  <AnchorPointX>0.5</AnchorPointX>
                  <AnchorPointY>0.0</AnchorPointY>
                </AnchorPoint>
                <Displacement>
                  <DisplacementX>0</DisplacementX>
                  <DisplacementY>5</DisplacementY>
                </Displacement>
              </PointPlacement>
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
          <Title>Junctions Division 4</Title>
          <ogc:Filter>
            <ogc:And>
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
                  <CssParameter name="fill">
                    <ogc:Function name="env">
                      <ogc:Literal>color4</ogc:Literal>
                      <ogc:Literal>{{ color4|default('#FFFF00') }}</ogc:Literal>
                    </ogc:Function>
                  </CssParameter>
                </Fill>
              </Mark>
              <Size>6</Size>
            </Graphic>
          </PointSymbolizer>
          {% if is_label_style %}
          <TextSymbolizer>
            <Label>
              <PropertyName>{{ variable }}</PropertyName>
            </Label>
            <Font>
              <CssParameter name="font-size">12</CssParameter>
            </Font>
            <LabelPlacement>
              <PointPlacement>
                <AnchorPoint>
                  <AnchorPointX>0.5</AnchorPointX>
                  <AnchorPointY>0.0</AnchorPointY>
                </AnchorPoint>
                <Displacement>
                  <DisplacementX>0</DisplacementX>
                  <DisplacementY>5</DisplacementY>
                </Displacement>
              </PointPlacement>
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
          <Title>Junctions Division 5</Title>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsGreaterThan>
                <ogc:PropertyName>{{ variable }}</ogc:PropertyName>
                <ogc:Function name="env">
                  <ogc:Literal>division4</ogc:Literal>
                  <ogc:Literal>{{ division4 }}</ogc:Literal>
                </ogc:Function>
              </ogc:PropertyIsGreaterThan>
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
                  <CssParameter name="fill">
                    <ogc:Function name="env">
                      <ogc:Literal>color5</ogc:Literal>
                      <ogc:Literal>{{ color5|default('#FF0000') }}</ogc:Literal>
                    </ogc:Function>
                  </CssParameter>
                </Fill>
              </Mark>
              <Size>6</Size>
            </Graphic>
          </PointSymbolizer>
          {% if is_label_style %}
          <TextSymbolizer>
            <Label>
              <PropertyName>{{ variable }}</PropertyName>
            </Label>
            <Font>
              <CssParameter name="font-size">12</CssParameter>
            </Font>
            <LabelPlacement>
              <PointPlacement>
                <AnchorPoint>
                  <AnchorPointX>0.5</AnchorPointX>
                  <AnchorPointY>0.0</AnchorPointY>
                </AnchorPoint>
                <Displacement>
                  <DisplacementX>0</DisplacementX>
                  <DisplacementY>5</DisplacementY>
                </Displacement>
              </PointPlacement>
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
        {% if variable != 'peakday_fireflow_available' %}
        <Rule>
          <Title>Tanks Division 1</Title>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsLessThan>
                <ogc:PropertyName>{{ variable }}</ogc:PropertyName>
                <ogc:Function name="env">
                  <ogc:Literal>division1</ogc:Literal>
                  <ogc:Literal>{{ division1 }}</ogc:Literal>
                </ogc:Function>
              </ogc:PropertyIsLessThan>
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
                  <CssParameter name="fill">
                    <ogc:Function name="env">
                      <ogc:Literal>color1</ogc:Literal>
                      <ogc:Literal>{{ color1|default('#0000FF') }}</ogc:Literal>
                    </ogc:Function>
                  </CssParameter>
                </Fill>
                <Stroke>
                  <CssParameter name="stroke">#FFFFFF</CssParameter>
                </Stroke>
              </Mark>
              <Size>15</Size>
            </Graphic>
          </PointSymbolizer>
          {% if is_label_style %}
          <TextSymbolizer>
            <Label>
              <PropertyName>{{ variable }}</PropertyName>
            </Label>
            <Font>
              <CssParameter name="font-size">12</CssParameter>
            </Font>
            <LabelPlacement>
              <PointPlacement>
                <AnchorPoint>
                  <AnchorPointX>0.5</AnchorPointX>
                  <AnchorPointY>0.0</AnchorPointY>
                </AnchorPoint>
                <Displacement>
                  <DisplacementX>0</DisplacementX>
                  <DisplacementY>5</DisplacementY>
                </Displacement>
              </PointPlacement>
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
          <Title>Tanks Division 2</Title>
          <ogc:Filter>
            <ogc:And>
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
                  <CssParameter name="fill">
                    <ogc:Function name="env">
                      <ogc:Literal>color2</ogc:Literal>
                      <ogc:Literal>{{ color2|default('#00FFFF') }}</ogc:Literal>
                    </ogc:Function>
                  </CssParameter>
                </Fill>
                <Stroke>
                  <CssParameter name="stroke">#FFFFFF</CssParameter>
                </Stroke>
              </Mark>
              <Size>15</Size>
            </Graphic>
          </PointSymbolizer>
          {% if is_label_style %}
          <TextSymbolizer>
            <Label>
              <PropertyName>{{ variable }}</PropertyName>
            </Label>
            <Font>
              <CssParameter name="font-size">12</CssParameter>
            </Font>
            <LabelPlacement>
              <PointPlacement>
                <AnchorPoint>
                  <AnchorPointX>0.5</AnchorPointX>
                  <AnchorPointY>0.0</AnchorPointY>
                </AnchorPoint>
                <Displacement>
                  <DisplacementX>0</DisplacementX>
                  <DisplacementY>5</DisplacementY>
                </Displacement>
              </PointPlacement>
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
          <Title>Tanks Division 3</Title>
          <ogc:Filter>
            <ogc:And>
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
                  <CssParameter name="fill">
                    <ogc:Function name="env">
                      <ogc:Literal>color3</ogc:Literal>
                      <ogc:Literal>{{ color3|default('#00FF00') }}</ogc:Literal>
                    </ogc:Function>
                  </CssParameter>
                </Fill>
                <Stroke>
                  <CssParameter name="stroke">#FFFFFF</CssParameter>
                </Stroke>
              </Mark>
              <Size>15</Size>
            </Graphic>
          </PointSymbolizer>
          {% if is_label_style %}
          <TextSymbolizer>
            <Label>
              <PropertyName>{{ variable }}</PropertyName>
            </Label>
            <Font>
              <CssParameter name="font-size">12</CssParameter>
            </Font>
            <LabelPlacement>
              <PointPlacement>
                <AnchorPoint>
                  <AnchorPointX>0.5</AnchorPointX>
                  <AnchorPointY>0.0</AnchorPointY>
                </AnchorPoint>
                <Displacement>
                  <DisplacementX>0</DisplacementX>
                  <DisplacementY>5</DisplacementY>
                </Displacement>
              </PointPlacement>
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
          <Title>Tanks Division 4</Title>
          <ogc:Filter>
            <ogc:And>
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
                  <CssParameter name="fill">
                    <ogc:Function name="env">
                      <ogc:Literal>color4</ogc:Literal>
                      <ogc:Literal>{{ color4|default('#FFFF00') }}</ogc:Literal>
                    </ogc:Function>
                  </CssParameter>
                </Fill>
                <Stroke>
                  <CssParameter name="stroke">#FFFFFF</CssParameter>
                </Stroke>
              </Mark>
              <Size>15</Size>
            </Graphic>
          </PointSymbolizer>
          {% if is_label_style %}
          <TextSymbolizer>
            <Label>
              <PropertyName>{{ variable }}</PropertyName>
            </Label>
            <Font>
              <CssParameter name="font-size">12</CssParameter>
            </Font>
            <LabelPlacement>
              <PointPlacement>
                <AnchorPoint>
                  <AnchorPointX>0.5</AnchorPointX>
                  <AnchorPointY>0.0</AnchorPointY>
                </AnchorPoint>
                <Displacement>
                  <DisplacementX>0</DisplacementX>
                  <DisplacementY>5</DisplacementY>
                </Displacement>
              </PointPlacement>
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
          <Title>Tanks Division 5</Title>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsGreaterThan>
                <ogc:PropertyName>{{ variable }}</ogc:PropertyName>
                <ogc:Function name="env">
                  <ogc:Literal>division4</ogc:Literal>
                  <ogc:Literal>{{ division4 }}</ogc:Literal>
                </ogc:Function>
              </ogc:PropertyIsGreaterThan>
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
                  <CssParameter name="fill">
                    <ogc:Function name="env">
                      <ogc:Literal>color5</ogc:Literal>
                      <ogc:Literal>{{ color5|default('#FF0000') }}</ogc:Literal>
                    </ogc:Function>
                  </CssParameter>
                </Fill>
                <Stroke>
                  <CssParameter name="stroke">#FFFFFF</CssParameter>
                </Stroke>
              </Mark>
              <Size>15</Size>
            </Graphic>
          </PointSymbolizer>
          {% if is_label_style %}
          <TextSymbolizer>
            <Label>
              <PropertyName>{{ variable }}</PropertyName>
            </Label>
            <Font>
              <CssParameter name="font-size">12</CssParameter>
            </Font>
            <LabelPlacement>
              <PointPlacement>
                <AnchorPoint>
                  <AnchorPointX>0.5</AnchorPointX>
                  <AnchorPointY>0.0</AnchorPointY>
                </AnchorPoint>
                <Displacement>
                  <DisplacementX>0</DisplacementX>
                  <DisplacementY>5</DisplacementY>
                </Displacement>
              </PointPlacement>
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
          <Title>Reservoirs Division 1</Title>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsLessThan>
                <ogc:PropertyName>{{ variable }}</ogc:PropertyName>
                <ogc:Function name="env">
                  <ogc:Literal>division1</ogc:Literal>
                  <ogc:Literal>{{ division1 }}</ogc:Literal>
                </ogc:Function>
              </ogc:PropertyIsLessThan>
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
                  <CssParameter name="fill">
                    <ogc:Function name="env">
                      <ogc:Literal>color1</ogc:Literal>
                      <ogc:Literal>{{ color1|default('#0000FF') }}</ogc:Literal>
                    </ogc:Function>
                  </CssParameter>
                </Fill>
                <Stroke>
                  <CssParameter name="stroke">#FFFFFF</CssParameter>
                </Stroke>
              </Mark>
              <Size>15</Size>
            </Graphic>
          </PointSymbolizer>
          {% if is_label_style %}
          <TextSymbolizer>
            <Label>
              <PropertyName>{{ variable }}</PropertyName>
            </Label>
            <Font>
              <CssParameter name="font-size">12</CssParameter>
            </Font>
            <LabelPlacement>
              <PointPlacement>
                <AnchorPoint>
                  <AnchorPointX>0.5</AnchorPointX>
                  <AnchorPointY>0.0</AnchorPointY>
                </AnchorPoint>
                <Displacement>
                  <DisplacementX>0</DisplacementX>
                  <DisplacementY>5</DisplacementY>
                </Displacement>
              </PointPlacement>
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
          <Title>Reservoirs Division 2</Title>
          <ogc:Filter>
            <ogc:And>
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
                  <CssParameter name="fill">
                    <ogc:Function name="env">
                      <ogc:Literal>color2</ogc:Literal>
                      <ogc:Literal>{{ color2|default('#00FFFF') }}</ogc:Literal>
                    </ogc:Function>
                  </CssParameter>
                </Fill>
                <Stroke>
                  <CssParameter name="stroke">#FFFFFF</CssParameter>
                </Stroke>
              </Mark>
              <Size>15</Size>
            </Graphic>
          </PointSymbolizer>
          {% if is_label_style %}
          <TextSymbolizer>
            <Label>
              <PropertyName>{{ variable }}</PropertyName>
            </Label>
            <Font>
              <CssParameter name="font-size">12</CssParameter>
            </Font>
            <LabelPlacement>
              <PointPlacement>
                <AnchorPoint>
                  <AnchorPointX>0.5</AnchorPointX>
                  <AnchorPointY>0.0</AnchorPointY>
                </AnchorPoint>
                <Displacement>
                  <DisplacementX>0</DisplacementX>
                  <DisplacementY>5</DisplacementY>
                </Displacement>
              </PointPlacement>
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
          <Title>Reservoirs Division 3</Title>
          <ogc:Filter>
            <ogc:And>
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
                  <CssParameter name="fill">
                    <ogc:Function name="env">
                      <ogc:Literal>color3</ogc:Literal>
                      <ogc:Literal>{{ color3|default('#00FF00') }}</ogc:Literal>
                    </ogc:Function>
                  </CssParameter>
                </Fill>
                <Stroke>
                  <CssParameter name="stroke">#FFFFFF</CssParameter>
                </Stroke>
              </Mark>
              <Size>15</Size>
            </Graphic>
          </PointSymbolizer>
          {% if is_label_style %}
          <TextSymbolizer>
            <Label>
              <PropertyName>{{ variable }}</PropertyName>
            </Label>
            <Font>
              <CssParameter name="font-size">12</CssParameter>
            </Font>
            <LabelPlacement>
              <PointPlacement>
                <AnchorPoint>
                  <AnchorPointX>0.5</AnchorPointX>
                  <AnchorPointY>0.0</AnchorPointY>
                </AnchorPoint>
                <Displacement>
                  <DisplacementX>0</DisplacementX>
                  <DisplacementY>5</DisplacementY>
                </Displacement>
              </PointPlacement>
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
          <Title>Reservoirs Division 4</Title>
          <ogc:Filter>
            <ogc:And>
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
                  <CssParameter name="fill">
                    <ogc:Function name="env">
                      <ogc:Literal>color4</ogc:Literal>
                      <ogc:Literal>{{ color4|default('#FFFF00') }}</ogc:Literal>
                    </ogc:Function>
                  </CssParameter>
                </Fill>
                <Stroke>
                  <CssParameter name="stroke">#FFFFFF</CssParameter>
                </Stroke>
              </Mark>
              <Size>15</Size>
            </Graphic>
          </PointSymbolizer>
          {% if is_label_style %}
          <TextSymbolizer>
            <Label>
              <PropertyName>{{ variable }}</PropertyName>
            </Label>
            <Font>
              <CssParameter name="font-size">12</CssParameter>
            </Font>
            <LabelPlacement>
              <PointPlacement>
                <AnchorPoint>
                  <AnchorPointX>0.5</AnchorPointX>
                  <AnchorPointY>0.0</AnchorPointY>
                </AnchorPoint>
                <Displacement>
                  <DisplacementX>0</DisplacementX>
                  <DisplacementY>5</DisplacementY>
                </Displacement>
              </PointPlacement>
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
          <Title>Reservoirs Division 5</Title>
          <ogc:Filter>
            <ogc:And>
              <ogc:PropertyIsGreaterThan>
                <ogc:PropertyName>{{ variable }}</ogc:PropertyName>
                <ogc:Function name="env">
                  <ogc:Literal>division4</ogc:Literal>
                  <ogc:Literal>{{ division4 }}</ogc:Literal>
                </ogc:Function>
              </ogc:PropertyIsGreaterThan>
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
                  <CssParameter name="fill">
                    <ogc:Function name="env">
                      <ogc:Literal>color5</ogc:Literal>
                      <ogc:Literal>{{ color5|default('#FF0000') }}</ogc:Literal>
                    </ogc:Function>
                  </CssParameter>
                </Fill>
                <Stroke>
                  <CssParameter name="stroke">#FFFFFF</CssParameter>
                </Stroke>
              </Mark>
              <Size>15</Size>
            </Graphic>
          </PointSymbolizer>
          {% if is_label_style %}
          <TextSymbolizer>
            <Label>
              <PropertyName>{{ variable }}</PropertyName>
            </Label>
            <Font>
              <CssParameter name="font-size">12</CssParameter>
            </Font>
            <LabelPlacement>
              <PointPlacement>
                <AnchorPoint>
                  <AnchorPointX>0.5</AnchorPointX>
                  <AnchorPointY>0.0</AnchorPointY>
                </AnchorPoint>
                <Displacement>
                  <DisplacementX>0</DisplacementX>
                  <DisplacementY>5</DisplacementY>
                </Displacement>
              </PointPlacement>
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
        {% endif %}
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>