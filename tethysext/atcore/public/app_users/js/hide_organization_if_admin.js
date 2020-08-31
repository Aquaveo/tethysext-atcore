function hide_organization_if_admin() {
    // Get data from page
    var $app_users_attributes = $('#app-users-attributes');
    var no_organization_roles = JSON.parse(
        $app_users_attributes.attr('data-no-organization-roles')
    );
    var selected_role = $('#assign-role option:selected').val();

    // Hide organization select if role cannot be assigned to an organization
    if (no_organization_roles.indexOf(selected_role) !== -1)
    {
        // Hide Organization Select
        $('#organization-select-wrapper').css('display', 'none');
    }
    else
    {
        // Show Organization Select
        $('#organization-select-wrapper').css('display', 'block');
    }
}

$('#assign-role').select2().on('change', function(e) {
    hide_organization_if_admin();
});

$(function() {
    // Hide Organization Select if admin
    hide_organization_if_admin();
});