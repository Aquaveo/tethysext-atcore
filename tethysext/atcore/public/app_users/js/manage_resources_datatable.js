/**
 * Initialize a client-side DataTable on the manage_resources table.
 *
 * All resource rows are rendered into the page by the server, and DataTables
 * handles searching, sorting, paging, and page-size selection in the browser.
 * Columns flagged with the "no-sort" class (select checkbox, organizations, and
 * the action-button column) are excluded from ordering and search.
 */
$(function () {
    var $table = $('#resource_table');

    if ($table.length === 0 || $.fn.DataTable.isDataTable($table)) {
        return;
    }

    var table = $table.DataTable({
        // "dom" omits the default search box ("f"); the custom, app-styled search input in the
        // page toolbar drives filtering instead. Layout: length menu, processing, table, info, paging.
        "dom": "lrtip",
        "order": [],
        "pageLength": 10,
        "lengthMenu": [5, 10, 20, 40, 80, 120],
        "stateSave": true,
        "columnDefs": [
            {"orderable": false, "searchable": false, "targets": "no-sort"}
        ]
    });

    // Wire the custom toolbar search input to the DataTable's client-side search.
    var $input = $('#resource-search-input');
    var $clear = $('#resource-search-clear');

    function syncClearButton(value) {
        $clear.toggleClass('d-none', !value);
    }

    // Restore any search term remembered by stateSave.
    var savedSearch = table.search();
    if (savedSearch) {
        $input.val(savedSearch);
        syncClearButton(savedSearch);
    }

    $input.on('keyup', function () {
        table.search(this.value).draw();
        syncClearButton(this.value);
    });

    $clear.on('click', function () {
        $input.val('');
        table.search('').draw();
        syncClearButton('');
    });

    // Bootstrap tooltips must be re-initialized after each redraw because
    // DataTables re-attaches row elements when paging/searching/sorting.
    table.on('draw', function () {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (el) {
            return bootstrap.Tooltip.getOrCreateInstance(el);
        });
    });
});
