$(function() {
    $('#workflow-form').on('submit', function(e) {
        // Add names to select boxes
        $('#workflow-form select').each(function() {
            $(this).attr('name', 'param-form-' + $(this).prev('label').text().toLowerCase().replace(' ', '_'));
        });
    });
});