// Dynamic querying select2 for SRID
$(function() {
    $(".js-query-srid-ajax").select2({
      // todo: implement when generalizing srid stuff
      ajax: {
        url: "/apps/epanet/processing/query-srid-by-query/",
        delay: 1000,
        data: function (params) {
          return {
            q: params['term'], // search term
          };
        },
        processResults: function (data, params) {
          return {
            results: data.results,
          };
        },

      },
      minimumInputLength: 2,
      placeholder: "No Basemap Available If Left Blank",
      allowClear: true,
    });
});