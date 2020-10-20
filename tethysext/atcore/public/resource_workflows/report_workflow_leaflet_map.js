// Create leaflet map.
var map = new L.Map('map').setView([-41.59490508367679, 146.77734375000003], 7);

// Create & add OSM layer.
var osm = new L.TileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png').addTo(map);

// Create & add WMS-layer.
var tasmania = new L.TileLayer.WMS('http://demo.opengeo.org/geoserver/wms', {
  layers: 'topp:tasmania',
  format: 'image/png',
  transparent: true,
  version: '1.3.0',
  crs: L.CRS.EPSG4326
}).addTo(map);

// Request preferred info format.
tasmania.getInfoFormat({
  done: function(infoFormat) {
  console.log('getInfoFormat succeed: ', infoFormat);
  },
  fail: function(errorThrown) {
  console.log('getInfoFormat failed: ', errorThrown);
  },
  always: function() {
  console.log('getInfoFormat finished');
  }
});