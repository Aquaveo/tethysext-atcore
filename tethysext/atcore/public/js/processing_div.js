/********************************************************************************
 * Name: main.js
 * Author: ntaylor, htran, msouffront
 * Created On: January 20, 2021
 * Copyright: (c) January 20, 2021
 * License:
 ********************************************************************************/

//Global setTimeout variables so that it can be cleared
var timeoutRefresh = null;
var timeoutInitial = null;
var ctrlIsPressed = false;

function addProcessingDiv() {
    var divShow = document.createElement("showBackground");
    var imageShow = document.createElement("showImage");
    var elem = document.createElement("img");

    if ($('#showBackground').length === 0) {
        divShow.id = 'showBackground';
        divShow.className="center-parent hidden";
        document.body.appendChild(divShow);
        imageShow.id = 'showImage';
        document.getElementById("showBackground").appendChild(imageShow);
        elem.setAttribute("src", "/static/atcore/images/loading3.gif");
        elem.setAttribute("height", "50");
        elem.setAttribute("width", "400");
        elem.setAttribute("alt", "Upload");
        document.getElementById("showImage").appendChild(elem);
    }
}


// Generate a GIF that covers page while loading
function showProcessing() {
    $('#showBackground').removeClass('hidden');
    console.log('here');
}

function hideProcessing() {
    $('#showBackground').addClass('hidden');
}


$(function(){
  $(document).on('click', 'input[type="submit"]', function () {
      if ($(this).closest('form').attr('target') !== '_blank') {
          showProcessing();
      }
  });

  window.onbeforeunload = function(e) {
    showProcessing();
  }

  addProcessingDiv();
});