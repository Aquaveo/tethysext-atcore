function show_message_box(id, level, message) {
    let message_box = '<div id="' + id + '" class="alert alert-' + level + ' alert-dismissible" role="alert">'
                    +   '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>'
                    +   message
                    + '</div>';
    let app_content_selector = '#app-content';
    let flash_messages_selector = app_content_selector + ' .flash-messages';
    let message_box_selector = flash_messages_selector + ' #' + id;

    if (!$(flash_messages_selector).length) {
        $(app_content_selector).append('<div class="flash-messages"></div>')
    }

    if (!$(message_box_selector).length) {
        $(flash_messages_selector).append(message_box);
    }
}