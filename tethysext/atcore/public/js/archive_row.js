function init_archive_row_buttons() {
  var csrf_token = get_csrf_token();

  // Remove previous handlers
  $('.btn-archive-manage').off();
  $('#modal-archive-button').off();

  // Bind on-click events to archive buttons on each row
  $('.btn-archive-manage').each(function(index, element){
      $(element).on('click', function(event) {
        var id = $(event.target).attr('data-id');
        // Clicked on the icon, not the button, so get id from the parent
        if (typeof id == 'undefined') {
            id = $(event.target).closest('.btn-archive-manage').attr('data-id');
        }

        // Set the id data attribute in modal to match id of row
        $('#modal-archive-button').attr('data-id', id);

        // Open the archive modal
        $('#archive-modal').modal('show');
      });
  });

  // Bind on-click events to archive button in modal
  $('#modal-archive-button').on('click', function(event) {
      var id = $(event.target).attr('data-id');
      var data = $(event.target).data();
      data.action = 'archive';
      var data_params = $.param(data);

      // Show loading dots
      $('#archive-modal .modal-footer').html('<img src="/static/atcore/images/loading-dots-small.gif">');

      // Send DELETE request
      $.ajax({
        method: 'DELETE',
        url: `?${data_params}`,
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
}

$(document).ready(function(){
  init_archive_row_buttons();
});
