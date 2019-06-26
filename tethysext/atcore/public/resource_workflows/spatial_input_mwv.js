/*****************************************************************************
 * FILE:    spatial_input_mwv.js
 * DATE:    June 21, 2019
 * AUTHOR:  Nathan Swain
 * COPYRIGHT: (c) Aquaveo 2019
 * LICENSE:
 *****************************************************************************/

/*****************************************************************************
 *                      LIBRARY WRAPPER
 *****************************************************************************/

var SPATIAL_INPUT_MWV = (function() {
	// Wrap the library in a package function
	"use strict"; // And enable strict mode for this library

	/************************************************************************
 	*                      MODULE LEVEL / GLOBAL VARIABLES
 	*************************************************************************/
 	// Module variables
 	var m_public_interface;				// Object returned by the module

 	// Map elements
    var m_current_layer,
        m_current_feature;

 	// Selectors
 	var m_id_attributes_wrapper =       'spatial-attributes',
 	    m_sel_attributes_template =     '#spatial-attributes-template',
 	    m_sel_attributes_wrapper =      '#' + m_id_attributes_wrapper,
 	    m_sel_attributes_form =         m_sel_attributes_wrapper + ' .spatial-attributes-form',
 	    m_sel_cancel_button =           '.spatial-attributes-cancel',
 	    m_sel_ok_button =               '.spatial-attributes-ok',
 	    m_sel_props_popup_container =   '#properties-popup',
 	    m_sel_attributes_error =        '#spatial-attributes .spatial-attributes-error';

	/************************************************************************
 	*                    PRIVATE FUNCTION DECLARATIONS
 	*************************************************************************/
 	var reset;

 	var generate_attributes_form, initialize_attributes_form, bind_attributes_ok,
 	    bind_popup_shown_event, bind_popup_closed_event;

 	var process_attributes_form;

 	reset = function() {
 	    m_current_feature = null;
        m_current_layer = null;
 	};

 	generate_attributes_form = function(feature, layer) {
 	    // Create attribute from from template
 	    let attributes_form = $(m_sel_attributes_template).clone();
 	    attributes_form.prop('id', m_id_attributes_wrapper);

 	    // Current property values
 	    let properties = feature.getProperties();

 	    for (let property in properties) {
 	        let form_field = attributes_form.find('[name=' + property + ']');
 	        form_field.val(properties[property]);
 	    }

 	    // Stash current layer and feature for later use
 	    m_current_layer = layer;
 	    m_current_feature = feature;

        return attributes_form;
    };

    process_attributes_form = function() {
        // Clear error messages
        $(m_sel_attributes_error).html('');

        // Serialize the form
        let data = $(m_sel_props_popup_container).find(m_sel_attributes_form).serializeArray();

        // Prepare ajax call
        data.push({'name': 'method', 'value': 'validate-feature-attributes'});

        $.ajax({
            method: 'POST',
            url:'',
            data: data,
        }).done(function(response){
            if (response.success) {
                // Assign as properties to current feature
                data.forEach(function(attribute, index) {
                    // Skip the csrf token and method
                    if (attribute.name == 'csrfmiddlewaretoken' || attribute.name == 'method') { return; }
                    let property = {};
                    property[attribute.name] = attribute.value;
                    m_current_feature.set(attribute.name, attribute.value);
                });

                // Close popup and deselect
                ATCORE_MAP_VIEW.close_properties_pop_up();
            } else {
                // Display error message to user
                $(m_sel_attributes_error).html(response.error);

                // Scroll to top of form div
                $(m_sel_attributes_form).scrollTop(0);
            }
        });
    };

    initialize_attributes_form = function() {
 	    // Bind to form buttons
 	    bind_attributes_ok();
 	};

    bind_attributes_ok = function() {
        // Bind actions to pop-up buttons
        $(m_sel_ok_button).off('click');
        $(m_sel_ok_button).on('click', function(){
            process_attributes_form();
            return false;
        });
    };

    bind_popup_shown_event = function() {
        $(m_sel_props_popup_container).on('shown.atcore.popup', function(e) {
            // Focus on first element in the form when form is shown
 	        $(m_sel_attributes_form + ':first *:input[type!=hidden]:first').select();
        });
    };

    bind_popup_closed_event = function() {
        $(m_sel_props_popup_container).on('closed.atcore.popup', function(e) {
            // Reset when the popup container is closed
            reset();
        });
    };

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
	m_public_interface = {};

	/************************************************************************
 	*                  INITIALIZATION / CONSTRUCTOR
 	*************************************************************************/

	// Initialization: jQuery function that gets called when
	// the DOM tree finishes loading
	$(function() {
	    // Init member variables
	    reset();

        // Override normal properties table
	    ATCORE_MAP_VIEW.properties_table_generator(function(feature, layer) { return ''; });

	    // Add attributes form to the properties pop-up
        ATCORE_MAP_VIEW.custom_properties_generator(generate_attributes_form);
        ATCORE_MAP_VIEW.custom_properties_initializer(initialize_attributes_form);

        // Bind to various popup events
        bind_popup_shown_event();
        bind_popup_closed_event();
	});

	return m_public_interface;

}()); // End of package wrapper
// NOTE: that the call operator (open-closed parenthesis) is used to invoke the library wrapper
// function immediately after being parsed.