function enable_tooltips() {
    $('[data-bs-toggle="tooltip"]').tooltip();
    $('[data-tooltip="tooltip"]').tooltip();
}

$(enable_tooltips);