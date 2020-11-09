$(function() {
    $('.resultType-map').each(function(i, obj) {
        wmsSources[i] = new ol.source.ImageWMS({url: $(obj).data("layer-url"),
            params: JSON.parse($(obj).data("layer-params").replace(/'/g, '"')),
            ratio: 1,
            serverType: 'geoserver',
        });
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
            layers: [
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
                }),
                new ol.layer.Image({
                    source: wmsSources[i],
                }),
            ],
            target: `openLayerMap${i+1}`,
            view: new ol.View({
                center: ol.proj.fromLonLat([($(obj).data("layer-extent")[0] + $(obj).data("layer-extent")[2])/2, ($(obj).data("layer-extent")[1] + $(obj).data("layer-extent")[3])/2]),
                zoom: 12,
            }),
        });

        // Find wms layer extent and fit the map to it.
        extents[i] = ol.proj.transformExtent($(obj).data("layer-extent"), 'EPSG:4326', 'EPSG:3857');
        maps[i].getView().fit(extents[i], maps[i].getSize());
    });
});