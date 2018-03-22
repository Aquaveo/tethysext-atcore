$(document).ready(function(){
  var delete_type = $('#modal-delete-button').attr('data-delete-type');
  var csrf_token = $('input[name=csrfmiddlewaretoken]').val();

  // Delete modal
  $('.btn-delete-manage').each(function(index, element){
      $(element).on('click', function(event) {
        var id = $(event.target).attr('data-id');
        if (typeof id == 'undefined') {
            // Selected the icon, not the button, so find the parent
            id = $(event.target).closest('.btn-delete-manage').attr('data-id');
        }
        $('#modal-delete-button').attr('data-id', id);
        $('#delete-modal').modal();
      });
  });

  $('#modal-delete-button').on('click', function(event) {
      var id = $(event.target).attr('data-id');
      var action = 'delete';

      // Show loading dots
      $('#delete-modal .modal-footer').html('<img src="/static/epanet/images/loading-dots-small.gif">');

      // Call delete
      $.ajax({
        method: 'DELETE',
        url: `?id=${id}&action=${action}`,
        beforeSend: xhr => {
            xhr.setRequestHeader('X-CSRFToken', csrf_token);
        },
      }).done(function(response) {
        if (response.success) {
            // Refresh the page when done
            location.reload();
        } else {
            console.log(response.error);
        }
      });
  });

  // Remove modal
  $('.btn-remove-user').each(function(index, element){
      $(element).on('click', function(event) {
        var id = $(event.target).attr('data-id');

        if (typeof id == 'undefined') {
            // Selected the icon, not the button, so find the parent
            id = $(event.target).closest('.btn-remove-user').attr('data-id');
        }

        $('#modal-remove-button').attr('data-id', id);
        $('#remove-modal').modal();
      });
  });

  $('#modal-remove-button').on('click', function(event) {
      var id = $(event.target).attr('data-id');
      var action = 'remove';

      // Show loading dots
      $('#remove-modal .modal-footer').html('<img src="/static/epanet/images/loading-dots-small.gif">');

      // Call remove
      $.ajax({
        method: 'DELETE',
        url: `?id=${id}&action=${action}`,
        beforeSend: xhr => {
            xhr.setRequestHeader('X-CSRFToken', csrf_token);
        },
      }).done(function(response) {
        if (response.success) {
            // Refresh the page when done
            location.reload();
        } else {
            console.log(response.error);
        }
      });
  });
});