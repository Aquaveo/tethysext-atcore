$(function() {
    var layers = [], maps = [], extent;
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
    var style_function = function (feature) {
        return styles[feature.getGeometry().getType()];
    };

    var base_layers = [
        new ol.layer.Tile({
            source: new ol.source.XYZ({
                attributions: 'Tiles © <a href="https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer">ArcGIS</a>',
                url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                crossOrigin: "anonymous",
            }),
        }),
        new ol.layer.Tile({
            source: new ol.source.XYZ({
                attributions: 'Tiles © <a href="https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer">ArcGIS</a>',
                url: 'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
                crossOrigin: "anonymous",
            }),
        })];


    $('.resultType-map').each(function(i, obj) {
        layers = [...base_layers];
        var layer_extent = '';
        var map_data = $(obj).data('map-layer-variables');
        map_data.forEach(function(data) {
            if (data['source'] == 'TileWMS' || data['source'] == 'ImageWMS') {
                layers.push(new ol.layer.Image({
                                source: new ol.source.ImageWMS({
                                    url: data.options.url,
                                    params: JSON.parse(JSON.stringify(data.options.params).replace(/'/g, '"')),
                                    ratio: 1,
                                    serverType: 'geoserver',
                                    crossOrigin: "anonymous",
                                })
                            })
                );
            }
            if (data['source'] == 'GeoJSON') {
                layers.push(new ol.layer.Vector({
                                style: style_function,
                                source: new ol.source.Vector({
                                    features: new ol.format.GeoJSON({featureProjection: 'EPSG:3857'}).readFeatures(data.options),
                                })
                            })
                );
            }
            layer_extent = layer_extent || data.legend_extent;
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
        extent = ol.proj.transformExtent(layer_extent, 'EPSG:4326', 'EPSG:3857');
        maps[i].getView().fit(extent, maps[i].getSize());
    });

    // Generate PDF
    $("#btnPDF").on('click', function () {
        var btn_pdf = document.getElementById('btnPDF');
        btn_pdf.disabled = true;
        var element = document.getElementById('report_workflow_data');
        var workflow_name = document.getElementById('workflow_name').value;
        workflow_name += ".pdf";
        var opt = {
          margin:       0.3,
          filename:     workflow_name,
          image:        { type: 'jpeg', quality: 1},
          html2canvas:  { dpi: 192, scale: 4, letterRenderding: true, },
          jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' },
          pagebreak:    { mode: 'avoid-all'}
        };
        html2pdf().set(opt).from(element).toPdf().save();
        btn_pdf.disabled = false;
    });

    // Print report
    $("#btnPrint").on("click", function() {
        let curURL = window.location.href;
        history.replaceState(history.state, '', '/report');
        window.print();
        history.replaceState(history.state, '', curURL);
    });
});