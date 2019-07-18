                                                   /*****************************************************************************
 * FILE:    spatial_data_mwv.js
 * DATE:    March 5, 2019
 * AUTHOR:  Nathan Swain
 * COPYRIGHT: (c) Aquaveo 2019
 * LICENSE:
 *****************************************************************************/

/*****************************************************************************
 *                      LIBRARY WRAPPER
 *****************************************************************************/

var SPATIAL_DATA_MWV = (function() {
	// Wrap the library in a package function
	"use strict"; // And enable strict mode for this library

	/************************************************************************
 	*                      MODULE LEVEL / GLOBAL VARIABLES
 	*************************************************************************/
 	// Module variables
 	var m_public_interface;				// Object returned by the module

 	var m_map;                          // OpenLayers map object

 	var m_data_popup_overlay,          // OpenLayers overlay containing the spatial data popup
        m_$data_popup_container,       // Spatial data popup container element
        m_$data_popup_content,         // Spatial data popup content element
        m_$data_popup_closer,          // Spatial data popup close button
        m_data_popup_loading_gif;      // Loading gif content

	/************************************************************************
 	*                    PRIVATE FUNCTION DECLARATIONS
 	*************************************************************************/
    var setup_map;

    var init_data_popup, on_select_features, show_spatial_data_pop_up, hide_spatial_data_pop_up,
        reset_spatial_data_pop_up, save_data, after_form_load;

 	/************************************************************************
 	*                    PRIVATE FUNCTION IMPLEMENTATIONS
 	*************************************************************************/

    // Setup Map
    setup_map = function() {
        // Get handle on map
	    m_map = TETHYS_MAP_VIEW.getMap();
    };

    on_select_features = function(event) {
        let selected = event.selected;
        if (selected.length > 0) {
            let feature_id = selected[0].get('id');
            reset_spatial_data_pop_up();

            // Load the pop-up form data.
            m_$data_popup_content.load('?method=get-popup-form&&feature-id=' + feature_id, function() {
                // Hook for custom post processing after the form loads
                after_form_load();

                // Re-show the pop-up after loading to recenter it.
                show_spatial_data_pop_up(selected);
            });

            // Show pop-up with the loading gif quickly to give user quick response
            show_spatial_data_pop_up(selected);
        } else {
            reset_spatial_data_pop_up();
        }
    };

    init_data_popup = function() {
        m_$data_popup_container = $('#spatial-data-popup');
        m_$data_popup_content = $('#spatial-data-form');
        m_$data_popup_closer = $('#spatial-data-popup-close-btn');
        m_data_popup_loading_gif = m_$data_popup_content.html();

        // Create new overlay for map
        m_data_popup_overlay = new ol.Overlay({
            element: m_$data_popup_container.get(0),
            autoPan: true,
            autoPanAnimation: {
                duration: 250
            }
        });

        // Add overlay to map
        m_map.addOverlay(m_data_popup_overlay);

        // Handle closer click events
        m_$data_popup_closer.on('click', function() {
            hide_spatial_data_pop_up();
            TETHYS_MAP_VIEW.clearSelection();
            return false;
        });

        // Unset Display None
        m_$data_popup_container.css('display', 'block');

        // Bind select interaction to spatial_data pop-up
        TETHYS_MAP_VIEW.getSelectInteraction().on('select', on_select_features);
    };

    show_spatial_data_pop_up = function(selected) {
        let popup_location = compute_center(selected);

        if (popup_location) {
            let coordinates = popup_location;

            if (popup_location instanceof ol.geom.Point) {
                coordinates = coordinates.getCoordinates();
            }
            m_data_popup_overlay.setPosition(coordinates);
        }
    };

    hide_spatial_data_pop_up = function() {
        m_data_popup_overlay.setPosition(undefined);
        m_$data_popup_closer.blur();
    };

    reset_spatial_data_pop_up = function() {
        hide_spatial_data_pop_up();
        m_$data_popup_content.html(m_data_popup_loading_gif);
    };

    save_data = function() {
        let $saf = $(m_$data_popup_content);
        let data = $saf.serialize();

        data = data + '&method=' + 'save-spatial-data';

        $.ajax({
            method: 'POST',
            url:'',
            data: data,
        }).done(function(response){
            console.log(response);
            hide_spatial_data_pop_up();
            TETHYS_MAP_VIEW.clearSelection();
        });

    };

    after_form_load = function() {};

	/************************************************************************
 	*                        DEFINE PUBLIC INTERFACE
 	*************************************************************************/
	/*
	 * Library object that contains public facing functions of the package.
	 * This is the object that is returned by the library wrapper function.
	 * See below.
	 * NOTE: The functions in the public interface have access to the private
	 * functions of the library because of JavaScript function scope.
	 */
	m_public_interface = {
	    'save_data': save_data,
	    'after_form_load': function(func) {
	        after_form_load = func;
	    },
	};

	/************************************************************************
 	*                  INITIALIZATION / CONSTRUCTOR
 	*************************************************************************/

	// Initialization: jQuery function that gets called when
	// the DOM tree finishes loading
	$(function() {
	    // Silence warning about leaving the page during ajax requests
	    window.onbeforeunload = null;
	    var enable_spatial_data = $('#spatial-data-attributes').data('enable-spatial-data-popup');
	    if (enable_spatial_data) {
	        setup_map();
            init_data_popup();
	    }
	});

	return m_public_interface;

}()); // End of package wrapper
// NOTE: that the call operator (open-closed parenthesis) is used to invoke the library wrapper
// function immediately after being parsed.