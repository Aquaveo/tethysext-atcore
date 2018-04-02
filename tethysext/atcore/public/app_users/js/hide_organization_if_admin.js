function hide_organization_if_admin() {
    var selected_val = $('#assign-role option:selected').val();

    // Owner select is not required for enterprise organizations
    if (selected_val == 'user_role_app_admin')
    {
        // Hide Owner Select
        $('#organization-select-wrapper').css('display', 'none');
    }
    else
    {
        // Show Owner Select
        $('#organization-select-wrapper').css('display', 'block');
    }
}

$('#assign-role').select2().on('change', function(e) {
    hide_organization_if_admin();
});

$(function() {
    // Hide owner if enterprise
    hide_organization_if_admin();
});