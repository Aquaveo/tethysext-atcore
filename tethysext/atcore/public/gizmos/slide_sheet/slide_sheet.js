/*****************************************************************************
 * FILE:    slide_sheet.js
 * DATE:    May 15, 2018
 * AUTHOR:  nswain
 * COPYRIGHT: (c) Aquaveo 2018
 * LICENSE:
 *****************************************************************************/

/*****************************************************************************
 *                      LIBRARY WRAPPER
 *****************************************************************************/

var SLIDE_SHEET = (function() {
    // Wrap the library in a package function
    "use strict"; // And enable strict mode for this library

    /************************************************************************
    *                      MODULE LEVEL / GLOBAL VARIABLES
    *************************************************************************/
    var public_interface;

    // Slide sheet
    var open_slide_sheet, close_slide_sheet;

    /************************************************************************
    *                    PRIVATE FUNCTION IMPLEMENTATIONS
    *************************************************************************/
    open = function(id) {
        $('#' + id + '.slide-sheet').addClass('show');
    };

    close = function(id) {
        $('#' + id + '.slide-sheet').removeClass('show');
    };


	/************************************************************************
 	*                        DEFINE PUBLIC INTERFACE
 	*************************************************************************/
	public_interface = {
		open: function(id) {
		    open(id);
		},
		close: function(id) {
		    close(id);
		},
	};

	/************************************************************************
 	*                  INITIALIZATION / CONSTRUCTOR
 	*************************************************************************/

	// Initialization: jQuery function that gets called when
	// the DOM tree finishes loading
	$(document).ready(function(){});

	return public_interface;

}()); // End of package wrapper
// NOTE: that the call operator (open-closed parenthesis) is used to invoke the library wrapper
// function immediately after being parsed.