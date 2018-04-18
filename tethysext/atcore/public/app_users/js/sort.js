$(function () {
    $('.table-sortable').find('thead').find('th').on('click', function () {
        var sortable_header = $(this).find('.sortable');
        
        if (sortable_header.length > 0) {
            var val = sortable_header.attr('data-sort-field');
            var inner_html = $(this).html();
            var search = window.location.search;
            var new_search;

            if (inner_html.indexOf('glyphicon') > -1 && inner_html.indexOf('-alt') === -1) {
                val += ':reverse';
            }

            if (search != '') {
                if (search.indexOf('sort_by=') > -1) {
                    new_search = search.replace(search.split('sort_by=')[1].split('&')[0], val);
                } else {
                    new_search = search += '&sort_by=' + val;
                }
            } else {
                new_search = search += '?sort_by=' + val;
            }

            window.location.search = new_search;
        }
    });
});