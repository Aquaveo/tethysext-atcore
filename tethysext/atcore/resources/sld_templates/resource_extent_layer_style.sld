<?xml version="1.0" encoding="UTF-8"?>
<sld:StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:sld="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:gml="http://www.opengis.net/gml" version="1.0.0">
    <sld:NamedLayer>
        <sld:Name>Default Styler</sld:Name>
        <sld:UserStyle>
            <sld:Name>Default Styler</sld:Name>
            <sld:Title>Resource Extent</sld:Title>
            <sld:Abstract>Extent of a Resource</sld:Abstract>
            <sld:FeatureTypeStyle>
                <sld:Name>name</sld:Name>
                <sld:Rule>
                    <sld:Name>Point</sld:Name>
                    <sld:Title>Resource Extent</sld:Title>
                    <sld:Abstract>Extent of a resource</sld:Abstract>
                    <ogc:Filter>
                        <ogc:PropertyIsEqualTo>
                            <ogc:Function name="geometryType">
                                <ogc:PropertyName>geometry</ogc:PropertyName>
                            </ogc:Function>
                            <ogc:Literal>Point</ogc:Literal>
                        </ogc:PropertyIsEqualTo>
                    </ogc:Filter>
                    <sld:PointSymbolizer>
                        <sld:Graphic>
                            <sld:Mark>
                                <sld:WellKnownName>circle</sld:WellKnownName>
                                <sld:Fill>
                                    <sld:CssParameter name="fill">#FFD400</sld:CssParameter>
                                </sld:Fill>
                            </sld:Mark>
                            <sld:Size>6</sld:Size>
                        </sld:Graphic>
                    </sld:PointSymbolizer>
                </sld:Rule>
                <sld:Rule>
                    <sld:Name>Polygon</sld:Name>
                    <sld:Title>Resource Extent</sld:Title>
                    <sld:Abstract>Extent of a resource</sld:Abstract>
                    <ogc:Filter>
                        <ogc:PropertyIsEqualTo>
                            <ogc:Function name="geometryType">
                                <ogc:PropertyName>geometry</ogc:PropertyName>
                            </ogc:Function>
                            <ogc:Literal>Polygon</ogc:Literal>
                        </ogc:PropertyIsEqualTo>
                    </ogc:Filter>
                    <sld:PolygonSymbolizer>
                        <sld:Stroke>
                            <sld:CssParameter name="stroke">#FFD400</sld:CssParameter>
                            <sld:CssParameter name="stroke-width">1</sld:CssParameter>
                        </sld:Stroke>
                    </sld:PolygonSymbolizer>
                </sld:Rule>
                <sld:Rule>
                    <sld:Name>Line</sld:Name>
                    <sld:Title>Resource Extent</sld:Title>
                    <sld:Abstract>Extent of a resource</sld:Abstract>
                    <ogc:Filter>
                        <ogc:PropertyIsEqualTo>
                            <ogc:Function name="geometryType">
                                <ogc:PropertyName>geometry</ogc:PropertyName>
                            </ogc:Function>
                            <ogc:Literal>Line</ogc:Literal>
                        </ogc:PropertyIsEqualTo>
                    </ogc:Filter>
                    <sld:LineSymbolizer>
                        <sld:Stroke>
                            <sld:CssParameter name="stroke">#FFD400</sld:CssParameter>
                            <sld:CssParameter name="stroke-width">3</sld:CssParameter>
                            <sld:CssParameter name="stroke-dasharray">5.0 2.0</sld:CssParameter>
                        </sld:Stroke>
                    </sld:LineSymbolizer>
                </sld:Rule>
            </sld:FeatureTypeStyle>
        </sld:UserStyle>
    </sld:NamedLayer>
</sld:StyledLayerDescriptor>