function hide_owner_if_enterprise() {
    var selected_val = $('#organization-type option:selected').val();

    // Owner select is not required for enterprise organizations
    if (selected_val == 'access_level_enterprise')
    {
        // Hide Owner Select
        $('#owner-select-wrapper').css('display', 'none');
    }
    else
    {
        // Show Owner Select
        $('#owner-select-wrapper').css('display', 'block');
    }
}

function show_appropriate_owners() {
    var selected_val = $('#organization-type option:selected').val();
    // LICENSE_TO_OWNER_MAPPING is set in modify_organization.html with a Django context variable
    var dictString = LICENSE_TO_OWNER_MAPPING.replace(/&quot;/g, '"');
    license_to_owner_mapping = JSON.parse(dictString);
    var owners_with_free_space_in_license = license_to_owner_mapping[selected_val];
    var selection_made = false;
    $('#organization-owner option')
        .prop('disabled', false)
        .each(function () {
            var firstEnabledId;
            var disabled = owners_with_free_space_in_license.indexOf(this.value) === -1

            if ($(this).is(':selected') && disabled) {
                firstEnabledId = $('#organization-owner option:enabled').not(this).first().val();
                $('#organization-owner').val(firstEnabledId).trigger('change');
            }

            $(this).prop('disabled', disabled);

            // Select2 must be reinitialized to accurately reflect changes
            $('#organization-owner').select2()
        });
}

$('#organization-type').select2().on('change', function(e) {
    hide_owner_if_enterprise();
    show_appropriate_owners();
});

$(function() {
    // Hide owner if enterprise
    hide_owner_if_enterprise();
    show_appropriate_owners();
});

