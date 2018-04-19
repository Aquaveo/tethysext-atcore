$(function() {
    $('.file-input').each(function(index) {
        var label = $(this).next('.btn-file-input'),
            label_val = $(label).html();

        $(this).on('change', function(e) {
            var filename = '',
                files = $(this).prop('files'),
                file_names = $.map(files, function(val) { return val.name; });

            if (file_names && file_names.length > 1) {
                filename = '{count} files selected'.replace('{count}', file_names.length);
            } else {
                filename = file_names[0];
            }

            if (filename) {
                $(label).html(filename);
            } else {
                $(label).html(label_val);
            }
        });
    });
});