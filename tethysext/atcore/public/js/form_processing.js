/********************************************************************************
 * Name: form_processing.js
 * Author: htran, msouffront
 * Created On: January 20, 2021
 * Copyright: (c) January 20, 2021
 * License:
 ********************************************************************************/

// Global setTimeout variables so that it can be cleared

function add_processing_div() {
    var div_show = document.createElement("div");
    var image_show = document.createElement("div");
    var elem = document.createElement("img");

    if ($('#show-background').length === 0) {
        div_show.id = 'show-background';
        div_show.className="center-parent d-none";
        document.body.appendChild(div_show);
        image_show.id = 'show-image';
        document.getElementById("show-background").appendChild(image_show);
        elem.setAttribute("src", "/static/atcore/images/loading3.gif");
        elem.setAttribute("alt", "Upload");
        document.getElementById("show-image").appendChild(elem);
    }
}


// Generate a GIF that covers page while loading
function show_processing() {
    $('#show-background').removeClass('d-none');
}

function hide_processing() {
    console.log()
    $('#show-background').addClass('d-none');
}


$(function(){
  $(document).on('click', 'input[type="submit"]', function () {
      if ($(this).closest('form').attr('target') !== '_blank') {
          show_processing();
      }
  });

  window.onbeforeunload = function(e) {
    show_processing();
  }

  add_processing_div();
});