function hide_consultant_if_not_allowed() {
    // Get data from page
    var $app_users_attributes = $('#app-users-attributes');
    var hide_consultant_licenses = JSON.parse(
        $app_users_attributes.attr('data-hide-consultant-licenses')
    );

    var selected_license = $('#organization-license option:selected').val();

    // Consultant select is not if the selected license does not
    // permit the organization to have a consultant
    if (hide_consultant_licenses.indexOf(selected_license) !== -1)
    {
        // Hide Consultant Select
        $('#consultant-select-wrapper').css('display', 'none');
    }
    else
    {
        // Show Consultant Select
        $('#consultant-select-wrapper').css('display', 'block');
    }
}

function show_appropriate_owners() {
    // Get data from page
    var $app_users_attributes = $('#app-users-attributes');
    var license_to_consultant_map = JSON.parse(
        $app_users_attributes.attr('data-license-to-consultant-map')
    );

    // Get selected license
    var selected_license = $('#organization-license option:selected').val();
    var consultants_can_add_client_with_license = license_to_consultant_map[selected_license];
    var selection_made = false;

    $('#organization-consultant option')
        .prop('disabled', false)
        .each(function () {
            var firstEnabledId;
            var disabled = consultants_can_add_client_with_license.indexOf(this.value) === -1

            if ($(this).is(':selected') && disabled) {
                firstEnabledId = $('#organization-consultant option:enabled').not(this).first().val();
                $('#organization-consultant').val(firstEnabledId).trigger('change');
            }

            $(this).prop('disabled', disabled);

            // Select2 must be reinitialized to accurately reflect changes
            $('#organization-consultant').select2();
        });
}

$('#organization-license').select2().on('change', function(e) {
    hide_consultant_if_not_allowed();
    show_appropriate_owners();
});

$(function() {
    // Hide owner if enterprise
    hide_consultant_if_not_allowed();
    show_appropriate_owners();
});

