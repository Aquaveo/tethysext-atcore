// Dynamic querying select2 for SRID
$(function() {
    $(".spatial-ref-select").each(function() {
        var $srs_attributes = $('#spatial-reference-service-attributes');
        var spatial_ref_url = JSON.parse($srs_attributes.attr('data-spatial-reference-service'));
        var placeholder = JSON.parse($srs_attributes.attr('data-placeholder'));
        var query_delay = JSON.parse($srs_attributes.attr('data-query-delay'));
        var min_length = JSON.parse($srs_attributes.attr('data-min-length'));

        $(this).select2({
            ajax: {
                url: spatial_ref_url,
                delay: query_delay,
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
            minimumInputLength: min_length,
            placeholder: placeholder,
            allowClear: true,
        });
    });
});