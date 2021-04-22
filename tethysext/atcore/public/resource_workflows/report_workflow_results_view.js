$(function() {
    var wmsSources = [], maps = [], extents = [], layers = [];
    var geojsonSources = [];
    var styles = {
        'Point': new ol.style.Style({
            image: new ol.style.Circle({
                        radius: 4,
                        fill: new ol.style.Fill({
                                color: 'red',
                              }),
                        stroke: new ol.style.Stroke({color: 'red', width: 1}),
                    }),
        }),
        'LineString': new ol.style.Style({
            stroke: new ol.style.Stroke({
                color: 'red',
                width: 2,
            }),
        }),
        'Polygon': new ol.style.Style({
            stroke: new ol.style.Stroke({
                color: 'red',
                width: 2,
            }),
            fill: new ol.style.Fill({
                color: 'rgba(255, 0, 0, 0.1)',
            }),
        }),
    }
    var styleFunction = function (feature) {
        return styles[feature.getGeometry().getType()];
    };

    var base_layers = [
        new ol.layer.Tile({
            source: new ol.source.XYZ({
                attributions: 'Tiles © <a href="https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer">ArcGIS</a>',
                url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            }),
        }),
        new ol.layer.Tile({
            source: new ol.source.XYZ({
                attributions: 'Tiles © <a href="https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer">ArcGIS</a>',
                url: 'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
            }),
        })]
    $('.resultType-map').each(function(i, obj) {
        layers = [...base_layers]
        var layer_extent = ''
        var map_data = $(obj).data('map-layer-variables')
        map_data.forEach(function(data) {
            if (data['source'] == 'TileWMS') {
                wmsSources[i] = new ol.source.ImageWMS({url: data.options.url,
                    params: JSON.parse(JSON.stringify(data.options.params).replace(/'/g, '"')),
                    ratio: 1,
                    serverType: 'geoserver',
                });
                layers.push(new ol.layer.Image({source: wmsSources[i]}))
            }
            if (data['source'] == 'GeoJSON') {
                layers.push(new ol.layer.Vector({
                                    style: styleFunction,
                                    source: new ol.source.Vector({
                                        features: new ol.format.GeoJSON({featureProjection: 'EPSG:3857'}).readFeatures(data.options),
                                    })
                                })
                            )
            }
            layer_extent = layer_extent || data.legend_extent
        })

        maps[i] = new ol.Map({
            controls: ol.control.defaults().extend([
                new ol.control.ScaleLine({
                    units: 'us',
                    bar: true,
                    steps: 4,
                    minWidth: 140,
                }),
                new ol.control.Rotate({
                    autoHide: false,
                    tipLabel: 'North Up',
                }),
            ]),
            layers: layers,
            target: `openLayerMap${i+1}`,
            view: new ol.View({
                center: ol.proj.fromLonLat([(layer_extent[0] + layer_extent[2])/2, (layer_extent[1] + layer_extent[3])/2]),
                zoom: 12,
            }),
        });

        // Find wms layer extent and fit the map to it.
        extents[i] = ol.proj.transformExtent(layer_extent, 'EPSG:4326', 'EPSG:3857');
        maps[i].getView().fit(extents[i], maps[i].getSize());
    });
});