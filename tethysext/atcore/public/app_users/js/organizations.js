$(function() {
  $('.input-group.spinner input.max-clients-spinner').on('change', function(e) {
    var input = e.target,
        organization_id = $(input).attr('data-organization-id'),
        access_level = $(input).attr('data-access-level'),
        value = $(input).val(),
        csrf_token = get_csrf_token(),
        url = '/apps/epanet/rest/organization/' + organization_id + '/' + access_level + '/set-max-clients/';

    var data = {
      'max_clients': value,
      'csrfmiddlewaretoken': csrf_token
    }

    $.ajax({
        method: 'post',
        url: url,
        data: data
    });
  });

  $('.input-group.spinner input.max-storage-spinner').on('change', function(e) {
    var input = e.target,
        organization_id = $(input).attr('data-organization-id'),
        value = $(input).val(),
        csrf_token = get_csrf_token(),
        url = '/apps/epanet/rest/organization/' + organization_id + '/set-max-storage/';

    var data = {
      'max_storage': value,
      'csrfmiddlewaretoken': csrf_token
    }

    $.ajax({
        method: 'post',
        url: url,
        data: data
    });
  });

  $('.addon-toggle').bootstrapSwitch();

  $('.addon-toggle').on('switchChange.bootstrapSwitch', function(e, value) {
    var input = e.target,
        organization_id = $(input).attr('data-organization-id'),
        addon = $(input).attr('name'),
        csrf_token = get_csrf_token(),
        url = '/apps/epanet/rest/organization/' + organization_id + '/trigger-addon/';

    var data = {
      'addon_key': addon,
      'value': value,
      'csrfmiddlewaretoken': csrf_token
    }

    $.ajax({
        method: 'post',
        url: url,
        data: data
    });
  });
});