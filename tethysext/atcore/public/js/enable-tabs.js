$(function() {
    var tab_selector = '.nav-tabs a';
    if (typeof TAB_SELECTOR !== 'undefined') {
        tab_selector = TAB_SELECTOR;
    }

    $(tab_selector).on('click', function(e) {
        e.preventDefault();
        $(this).tab('show');
    });
});