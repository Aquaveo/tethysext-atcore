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
 	var m_sel_attributes_template =     '#spatial-attributes-template',
 	    m_sel_attributes_wrapper =      '#spatial-attributes',
 	    m_sel_attributes_form =         '.spatial-attributes-form',
 	    m_sel_cancel_button =           '.spatial-attributes-cancel',
 	    m_sel_ok_button =               '.spatial-attributes-ok',
 	    m_sel_props_popup_container =   '#properties-popup';

	/************************************************************************
 	*                    PRIVATE FUNCTION DECLARATIONS
 	*************************************************************************/
 	var reset;

 	var generate_attributes_form, initialize_attributes_form, bind_attributes_cancel, bind_attributes_ok,
 	    bind_popup_close_event;

 	var process_attributes_form;

 	reset = function() {
 	    m_current_feature = null;
        m_current_layer = null;
 	};

 	generate_attributes_form = function(feature, layer) {
 	    // Create attribute from from template
 	    let attributes_form = $(m_sel_attributes_template).clone();
 	    attributes_form.prop('id', m_sel_attributes_wrapper);

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
        let data = $(m_sel_props_popup_container).find(m_sel_attributes_form).serializeArray();
        data.forEach(function(attribute, index) {
            let property = {};
            property[attribute.name] = attribute.value;
            m_current_feature.set(attribute.name, attribute.value);
        });
    };

    initialize_attributes_form = function() {
 	    bind_attributes_cancel();
 	    bind_attributes_ok();
 	};

    bind_attributes_cancel = function() {
        // Bind actions to pop-up buttons
        $(m_sel_cancel_button).off('click');
        $(m_sel_cancel_button).on('click', function(){
            ATCORE_MAP_VIEW.close_properties_pop_up();
            return false;
        });
    };

    bind_attributes_ok = function() {
        // Bind actions to pop-up buttons
        $(m_sel_ok_button).off('click');
        $(m_sel_ok_button).on('click', function(){
            process_attributes_form();
            ATCORE_MAP_VIEW.close_properties_pop_up();
            return false;
        });
    };

    bind_popup_close_event = function() {
        $(m_sel_props_popup_container).on('properties-popup:after-close', function(e) {
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

        bind_popup_close_event();
	});

	return m_public_interface;

}()); // End of package wrapper
// NOTE: that the call operator (open-closed parenthesis) is used to invoke the library wrapper
// function immediately after being parsed.