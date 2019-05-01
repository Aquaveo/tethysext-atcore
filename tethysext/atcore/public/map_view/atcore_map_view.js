/*****************************************************************************
 * FILE:    atcore_map_view.js
 * DATE:    October, 19, 2018
 * AUTHOR:  Nathan Swain
 * COPYRIGHT: (c) Aquaveo 2018
 * LICENSE:
 *****************************************************************************/

/*****************************************************************************
 *                      LIBRARY WRAPPER
 *****************************************************************************/

var ATCORE_MAP_VIEW = (function() {
	// Wrap the library in a package function
	"use strict"; // And enable strict mode for this library

	/************************************************************************
 	*                      MODULE LEVEL / GLOBAL VARIABLES
 	*************************************************************************/
 	// Constants
    var SELECTED_POINT_COLOR =           '#7300e5',
 	    SELECTED_LINE_COLOR =            '#7300e5',
 	    SELECTED_POLYGON_COLOR =         '#7300e5';

 	// Module variables
 	var m_public_interface;				// Object returned by the module

 	var m_map,                          // OpenLayers map object
 	    m_layers,                       // OpenLayers layer objects mapped to by layer by layer_name
 	    m_layer_groups,                 // Layer and layer group metadata
 	    m_workspace,                    // Workspace from SpatialManager
 	    m_extent,                       // Home extent for map
 	    m_enable_properties_popup,      // Show properties pop-up
 	    m_select_interaction;           // TethysMap select interaction for vector layers

 	var m_geocode_objects,              // An array of the current items in the geocode select
        m_geocode_layer;                // Layer used to store geocode location

    var m_props_popup_overlay,          // OpenLayers overlay containing the properties popup
        m_$props_popup_container,       // Properties popup container element
        m_$props_popup_content,         // Properties popup content element
        m_$props_popup_closer;          // Properties popup close button


    var m_plot,                         // Plot object
        m_plot_config;                  // Configuration options for the plot

    // Permissions
    var p_can_geocode,                  // Can use geocode feature
        p_can_plot;                     // Can use plotting feature

	/************************************************************************
 	*                    PRIVATE FUNCTION DECLARATIONS
 	*************************************************************************/
 	// Config
 	var parse_attributes, parse_permissions, setup_ajax, setup_map, csrf_token;

 	// Map management
 	var remove_layer_from_map, get_layer_name_from_feature, get_feature_id_from_feature;

 	// Action Button
 	var generate_action_button, bind_action_buttons, load_action

 	// Plotting
 	var init_plot, generate_plot_button, bind_plot_buttons, load_plot, fit_plot, update_plot, show_plot, hide_plot;

 	// Layers tab
 	var init_layers_tab, init_visibility_controls, init_opacity_controls, init_rename_controls, init_remove_controls,
 	    init_zoom_to_controls, init_collapse_controls, init_add_layer_controls, init_download_layer_controls,
 	    init_dropdown_layer_toggle_controls;

    // Properties pop-up
    var init_properties_pop_up, display_properties, show_properties_pop_up, hide_properties_pop_up,
        reset_properties_pop_up, append_properties_pop_up_content, reset_ui, generate_properties_table_title,
        generate_properties_table, generate_dataset_row;

 	// Feature selection
 	var init_feature_selection, points_selection_styler, lines_selection_styler, polygons_selection_styler,
 	    on_select_vector_features, on_select_wms_features;

 	// Action modal
 	var init_action_modal, build_action_modal, show_action_modal, hide_action_modal;

 	// Geocode feature
 	var init_geocode, do_geocode, clear_geocode;

 	// Cache methods
 	var is_in_cache, add_to_cache, remove_from_cache, get_from_cache;

 	// Drawing methods
 	var init_draw_controls;

 	// Utility Methods

 	var generate_uuid;

 	/************************************************************************
 	*                    PRIVATE FUNCTION IMPLEMENTATIONS
 	*************************************************************************/
    // Config
    parse_attributes = function() {
        var $map_attributes = $('#atcore-map-attributes');
        m_layer_groups = $map_attributes.data('layer-groups');
        m_extent = $map_attributes.data('map-extent');
        m_workspace = $map_attributes.data('workspace');
        m_enable_properties_popup = $map_attributes.data('enable-properties-popup');
    };

    parse_permissions = function() {
        var $map_permissions = $('#atcore-map-permissions');
        p_can_geocode = $map_permissions.data('can-use-geocode');
        p_can_plot = $map_permissions.data('can-use-plot');
    };

    setup_ajax = function() {
        // Ajax options
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                    // Only send the token to relative URLs i.e. locally.
                    xhr.setRequestHeader("X-CSRFToken", get_csrf_token());
                }
            }
        });
    };

    setup_map = function() {
        // Change Extent Button from "E" to Extent Symbol
        let $extent_button = $('button[title="Fit to extent"]');
        $extent_button.html('<span class="glyphicon glyphicon-home"></span>')

        // Get handle on map
	    m_map = TETHYS_MAP_VIEW.getMap();

	    // Set initial extent
	    TETHYS_MAP_VIEW.zoomToExtent(m_extent);

	    // Setup layer map
	    m_layers = {};

	    // Get id from tethys_data attribute
	    m_map.getLayers().forEach(function(item, index, array) {
	        if ('tethys_data' in item && 'layer_id' in item.tethys_data) {
	           if (item.tethys_data.layer_id in m_layers) {
	               console.log('Warning: layer_name already in layers map: "' + item.tethys_data.layer_id + '".');
	           }
	           m_layers[item.tethys_data.layer_id] = item;
	        }
	    });

	    // Setup feature selection
	    init_feature_selection();
    };

    // Map Management
    remove_layer_from_map = function(layer_name) {
        // Remove from map
        m_map.removeLayer(m_layers[layer_name]);

        // Remove from layers list
        delete m_layers[layer_name];
    };

    get_layer_name_from_feature = function(feature) {
        // Get layer_name from property of the feature
        let layer_name = feature.get('layer_name');

        // Attempt to derive layer name from ID assigned by GeoServer to be able to map to features to layers in map (<layer_name>.<fid>)
        // e.g.: 0958cc07-c194-4af9-81c5-118a77d335ac_stream_links.fid--72787a80_169a16811e6_-7aa6
        if (!layer_name) {
            let feature_id = feature.getId();
            layer_name = m_workspace + ':' + feature_id.split('.')[0];
        }

        return layer_name;
    };

    get_feature_id_from_feature = function(feature) {
        let feature_id = feature.getId();
        let fid = '-1';

        if (feature_id) {
            // Derive fid from ID assigned by GeoServer (<layer_name>.<fid>)
            // e.g.: 0958cc07-c194-4af9-81c5-118a77d335ac_stream_links.fid--72787a80_169a16811e6_-7aa6
            fid = feature_id.split('.')[1];
        } else {
            fid = feature.get('id');
        }

        return fid;
    };

    // Plotting
    init_plot = function() {
        // Skip if no permission to use plot
        if (!p_can_plot) {
            return;
        }

        m_plot = 'map-plot';
        m_plot_config = {scrollZoom: true};

        let data = [];

        let layout = {
            autosize: true,
            height: 415,
            margin: {l: 80, r: 80, t: 20, b: 80},
            xaxis:  {
                title: 'X Axis Title',
            },
            yaxis: {
                title: 'Y Axis Title',
            }
        };

        // Create initial plot
        update_plot('Plot Title', data, layout);

        // Setup plot resize when slide sheet changes size
        $(window).resize(function() {
            fit_plot();
        });

        // Resize plot when nav is opened or closed
        $('.toggle-nav').on('tethys:toggle-nav', function(e) {
            fit_plot();
        });
    };

    update_plot = function(title, data, layout) {
        let out = Plotly.validate(data, layout);
        if (out) {
            $(out).each(function(index, item) {
                console.error(item.msg);
            });
            return;
        }

        // Update plot
        Plotly.react(m_plot, data, layout, m_plot_config).then(function(p) {
            // Resize plot to fit after rendering the first time
            fit_plot();

            // Update slide sheet title
            $('#plot-slide-sheet .slide-sheet-title').html(title);
        });
    };

    generate_plot_button = function(feature) {
        // Skip if no permission to use plot
        if (!p_can_plot) {
            return;
        }
        let layer_name = get_layer_name_from_feature(feature);
        let fid = get_feature_id_from_feature(feature);
        // Check if layer is plottable
        let layer = m_layers[layer_name];
        if (!layer || !layer.tethys_data.plottable) {
            return;
        }

        // Build Plot Button Markup
        let plot_button =
            '<div class="plot-btn-wrapper">' +
                '<a class="btn btn-primary btn-popup" ' +
                    'href="javascript:void(0);" ' +
                    'role="button"' +
                    'data-feature-id="' + fid +'"' +
                    'data-layer-id="' + layer_name + '"' +
                '>Plot</a>' +
            '</div>';

        return plot_button;
    };

    generate_action_button = function(feature) {
        // Skip if no permission to use plot
        if (!p_can_plot) {
            return;
        }

        let layer_name = get_layer_name_from_feature(feature);
        let fid = get_feature_id_from_feature(feature);

        // Check if layer is has action
        let layer = m_layers[layer_name];
        if (!layer || !layer.tethys_data.has_action) {
            return;
        }

        // Build Action Button Markup
        let action_button =
            '<div class="action-btn-wrapper">' +
                '<a class="btn btn-primary btn-popup" ' +
                    'href="javascript:void(0);" ' +
                    'role="button"' +
                    'data-feature-id="' + fid +'"' +
                    'data-layer-id="' + layer_name + '"' +
                '>Action</a>' +
            '</div>';

        return action_button;
    };

    bind_plot_buttons = function() {
        // Reset click events on plot buttons
        $('.btn-plot').off('click');

        // Call load_plot when buttons are clicked
        $('.btn-plot').on('click', function(e) {
            let layer_name = $(e.target).data('layer-id');
            let feature_id = $(e.target).data('feature-id');

            // Load the plot
            load_plot(e.target, layer_name, feature_id);
        });
    };

    bind_action_buttons = function() {
        // Reset click events on plot buttons
        $('.btn-plot').off('click');

        // Call load_plot when buttons are clicked
        $('.btn-plot').on('click', function(e) {
            let layer_name = $(e.target).data('layer-id');
            let feature_id = $(e.target).data('feature-id');

            // Load the plot
            load_action(e.target, layer_name, feature_id);
        });
    };

    load_plot = function(plot_button, layer_name, feature_id) {
        // Disable plot button
        $(plot_button).attr('disabled', 'disabled');

        // Get plot data for feature
        $.ajax({
            url: '.',
            type: 'POST',
            data: {
                'method': 'get-plot-data',
                'layer_name': layer_name,
                'feature_id': feature_id
            },
        }).done(function(data){
            // Update plot
            update_plot(data.title, data.data, data.layout);

            // Show the plot slide sheet
            show_plot();

            // Enable plot button
            $(plot_button).removeAttr('disabled');
        });
    };

    load_action = function(action_button, layer_name, feature_id) {
        // Use public interface in Apps to customize action
    };

    fit_plot = function() {
        let plot_container_width = $('#plot-slide-sheet').width();
        Plotly.relayout(m_plot, {width: plot_container_width});
    };

    show_plot = function() {
        SLIDE_SHEET.open('plot-slide-sheet');
    };

    hide_plot = function() {
        SLIDE_SHEET.close('plot-slide-sheet');
    };

    // Action modal
    init_action_modal = function() {
        // Remove action button click events whenever modal hides
        $('#action-modal').on('hide.bs.modal', function(e) {
            let $modal_do_action_button = $('#action-modal #do-action-button');
            $modal_do_action_button.off('click');
        });

        // Enable autofocus on modal
        $('#action-modal').on('shown.bs.modal', function() {
            $(this).find('[autofocus]').focus();
        });
    };

    build_action_modal = function(modal_title, modal_content, modal_action, modal_style) {
        let $modal = $('#action-modal');
        let $modal_title = $('#action-modal #action-modal-title');
        let $modal_content = $('#action-modal #action-modal-content');
        let $modal_do_action_button = $('#action-modal #do-action-button');

        $modal_title.html(modal_title);
        $modal_content.html(modal_content);
        $modal_do_action_button.html(modal_action);
        $modal_do_action_button.attr('class', 'btn btn-' + modal_style);

        return {
            'modal': $modal,
            'title': $modal_title,
            'content': $modal_content,
            'action_button': $modal_do_action_button,
        };
    };

    show_action_modal = function() {
        let $modal = $('#action-modal');
        $modal.modal('show');
    };

    hide_action_modal = function() {
        let $modal = $('#action-modal');
        $modal.modal('hide');
    };

    // Layers tab methods
    init_layers_tab = function() {
        // Init controls
        init_action_modal();
        init_visibility_controls();
        init_opacity_controls();
        init_rename_controls();
        init_dropdown_layer_toggle_controls();
        init_remove_controls();
        init_zoom_to_controls();
        init_download_layer_controls();
        init_add_layer_controls();
        init_collapse_controls();
    };

    init_visibility_controls = function() {
        // Setup deselect event on radio buttons in layers menu
        let selected_radios = {};

        // Credits for radio deselect event: https://stackoverflow.com/questions/11173685/how-to-detect-radio-button-deselect-event
        $('input[type="radio"]').on('click', function() {
            if (this.name in selected_radios) {
                // A non-active radio button is clicked
                if (this != selected_radios[this.name]) {
                    // Fire the deselect event on the previously active radio button
                    $(selected_radios[this.name]).trigger("deselect");

                    // Save this radio as the new active radio button
                    selected_radios[this.name] = this;
                }
                // The the active radio is clicked again
                else {
                    // Uncheck the radio (like a checkbox)
                    this.checked = false;
                    // Fire the deselect event on the radio
                    $(this).trigger("deselect");
                    // No radio is selected in this group,
                    // so remove it from the selected radios object
                    delete selected_radios[this.name];
                }
            }
            else {
                // Save which radio was just checked on
                selected_radios[this.name] = this;
            }

        }).filter(':checked').each(function() {
            // Note initial state of radio buttons
            selected_radios[this.name] = this;
        });

        // Layer group visiblity
        $('.layer-group-visibility-control').on('change', function(e) {
            let $target = $(e.target);
            let layer_group_checked = $target.is(':checked');
            let $layer_group_item = $target.closest('.layer-group-item');
            let $layer_list = $layer_group_item.next('.layer-list');

            // Reset the ui
            reset_ui();

            // For each layer visibilty control...
            let $layer_visiblity_controls = $layer_list.find('.layer-visibility-control');

            $layer_visiblity_controls.each(function(index, item) {
                // Set disabiled
                let $item = $(item);
                $item.prop('disabled', !layer_group_checked);

                // Set layer visibility
                let layer_name = $item.data('layer-id');
                let layer_checked = $item.is(':checked');
                let layer_variable = $item.data('layer-variable');
                m_layers[layer_name].setVisible(layer_group_checked && layer_checked);

                if (layer_group_checked && layer_checked) {
                    $("#legend-" + layer_variable).removeClass('hidden')
                } else {
                    $("#legend-" + layer_variable).addClass('hidden')
                }

            });

            // For each context menu...
            let $layers_context_menu = $layer_list.find('.layers-context-menu');

            $layers_context_menu.each(function(index, item) {
                let $dropdown_toggle = $(item).find('.dropdown-toggle');

                if (layer_group_checked) {
                    $dropdown_toggle.removeClass('disabled');
                }

                else {
                    $dropdown_toggle.addClass('disabled');
                }
            });
        });

        // Layer visibility
        $('.layer-visibility-control').on('change', function(e) {
            let $target = $(e.target);
            let checked = $target.is(':checked');
            let layer_name = $target.data('layer-id');
            let layer_variable = $target.data('layer-variable');

            // Reset the ui
            reset_ui();

            // Set the visibility of layer
            m_layers[layer_name].setVisible(checked);

            // Set the visibility of legend
             $("#legend-" + layer_variable).removeClass('hidden')

            // TODO: Save state to resource - store in attributes?
        });

        // Handle radio deselect events
        $('.layer-visibility-control').on('deselect', function(e) {
            let $target = $(e.target);
            let checked = $target.is(':checked');
            let layer_name = $target.data('layer-id');
            let layer_variable = $target.data('layer-variable');

            // Set the visibility of layer
            m_layers[layer_name].setVisible(checked);

            // Set the visibility of legend
            $("#legend-" + layer_variable).addClass('hidden')

            // TODO: Save state to resource - store in attributes?
        });
    };

    init_opacity_controls = function() {
        // Handle changes to the opacity controls
        $('.layer-opacity-control').on('input', function(e) {
            let $target = $(e.target);
            let val = $target.val();

            // Update display value
            let $label = $target.prev('label');
            let $label_value = $label.children('.slider-value').first();
            $label_value.html(val + '%');

            // Update opacity of layer
            let layer_name = $target.data('layer-id');
            m_layers[layer_name].setOpacity(val/100);

            // TODO: Save state to resource - store in attributes?
        });
    };

    init_rename_controls = function() {
        // Rename layer
        $('.rename-action').on('click', function(e) {
            let $action_button = $(e.target);

            if (!$action_button.hasClass('rename-action')) {
                $action_button = $action_button.closest('.rename-action');
            }

            let $layer_label = $action_button.closest('.layers-context-menu').prev();
            let $display_name = $layer_label.find('.display-name').first();
            let current_name = $display_name.html();

            // Build Modal
            let modal_content = '<div class="form-group">'
                              +     '<label class="sr-only" for="new-name-field">New name:</label>'
                              +     '<input class="form-control" type="text" id="new-name-field" value="' + current_name + '" autofocus onfocus="this.select();">'
                              + '</div>';

            let modal = build_action_modal('Rename Layer', modal_content, 'Rename', 'success');

            // Show Modal
            show_action_modal();

            // Handle Modal Action
            modal.action_button.on('click', function(e) {
                // Rename layer label
                let new_name = modal.content.find('#new-name-field').first().val();
                $display_name.html(new_name);

                // Hide the modal
                hide_action_modal();

                // TODO: Save state to resource - store in attributes?
            });
        });
    };

    init_remove_controls = function() {
        $('.remove-action').on('click', function(e) {
            let $action_button = $(e.target);

            if (!$action_button.hasClass('remove-action')) {
                $action_button = $action_button.closest('.remove-action');
            }

            let remove_type = $action_button.data('remove-type');
            let $layer_label = $action_button.closest('.layers-context-menu').prev();
            let display_name = $layer_label.find('.display-name').first().html();

            // Build Modal
            let modal_title = '';
            let modal_content = '';
            if (remove_type === 'layer') {
                modal_title = 'Remove Layer'
                modal_content = '<p>Are you sure you want to remove the "' + display_name
                              + '" layer?</p>';
            } else {
                modal_title = 'Remove Layer Group'
                modal_content = '<p>Are you sure you want to remove the "' + display_name
                              + '" layer group and all of its layers?</p>';
            }

            let modal = build_action_modal(modal_title, modal_content, 'Remove', 'danger');

            // Show Modal
            show_action_modal();


            // Handle Modal Action
            modal.action_button.on('click', function(e) {
                // Reset the ui
                reset_ui();
                var uuid = ''
                if (remove_type === 'layer') {
                    // Remove layer from map
                    var layer_id = $action_button.data('layer-id');
                    remove_layer_from_map(layer_id);

                    // Remove item from layers tree
                    let layer_list_item = $action_button.closest('.layer-list-item');
                    layer_list_item.remove();
                }
                else {
                    // Remove layers from map
                    let $layer_group_item = $action_button.closest('.layer-group-item');
                    let $layer_list = $layer_group_item.next('.layer-list');

                    let $layer_visiblity_controls = $layer_list.find('.layer-visibility-control');

                    // Remove all layers in layer group
                    $layer_visiblity_controls.each(function(index, item) {
                        let layer_name = $(item).data('layer-id');
                        remove_layer_from_map(layer_name);
                    });

                    // Remove layer group item
                    $layer_group_item.remove();

                    // Remove layer list item
                    $layer_list.remove();
                }

                // Hide the modal
                hide_action_modal();

                // TODO: Save state to resource - store in attributes?
                // Save state of custom_layers to resource
                if (remove_type === 'layer') {
                    csrf_token = $('input[name=csrfmiddlewaretoken]').val()
                    $.ajax({
                        type: 'POST',
                        url: '',
                        data: {'method': 'remove_custom_layer',
                               'layer_group_type': 'custom_layers',
                               'layer_id': layer_id},
                        beforeSend: xhr => {
                            xhr.setRequestHeader('X-CSRFToken', csrf_token);
                        },
                    }).done(function (data) {

                    })
                }
            });
        });
    };

    init_dropdown_layer_toggle_controls = function() {
        // Rename layer
        $('.layer-dropdown-toggle').on('switchChange.bootstrapSwitch', function(e, state) {
            let $action_button = $(e.target);
            let $layer_label = $action_button.closest('.layers-context-menu').prev();
            let display_name = $layer_label.find('.display-name').first().html();

            // TODO: Implement
            // TODO: Save state to workflow - store in attributes?
        });
    };

    init_zoom_to_controls = function() {
        // Zoom to layer
        $('.zoom-to-layer-action').on('click', function(e) {
            let $action_button = $(e.target);

            if (!$action_button.hasClass('zoom-to-layer-action')) {
                $action_button = $action_button.closest('.zoom-to-layer-action');
            }

            let layer_name = $action_button.data('layer-id');
            let extent = m_layers[layer_name].getExtent();

            if (extent) {
                // Zoom to layer extent
                TETHYS_MAP_VIEW.zoomToExtent(extent);
            }
            else {
                // TODO: Query GeoServer to get layer extent?
                // Zoom to map extent if layer has no extent
                TETHYS_MAP_VIEW.zoomToExtent(m_extent);
            }
        });
    };

    init_collapse_controls = function() {
        $('.collapse-action').on('click', function(e) {
            let $action_button = $(e.target);

            if (!$action_button.hasClass('collapse-action')) {
                $action_button = $action_button.closest('.collapse-action');
            }

            let $layer_group_item = $action_button.closest('.layer-group-item');
            let $layer_list = $layer_group_item.next('.layer-list');
            let is_collapsed = $layer_list.data('collapsed') || false;

            if (is_collapsed) {
                expand_section($layer_list.get(0));
                $layer_list.data('collapsed', false);
                $action_button.data('collapsed', false);
            }
            else {
                collapse_section($layer_list.get(0));
                $layer_list.data('collapsed', true);
                $action_button.data('collapsed', true);
            }
        });
    };

    init_download_layer_controls = function() {
        // TODO: Implement
    };

    init_add_layer_controls = function() {
        $('.add-layer-to-layer-group').on('click', function(e) {
            let $action_button = $(e.target);

            if (!$action_button.hasClass('add-layer-to-layer-group')) {
                $action_button = $action_button.closest('.add-layer-to-layer-group');
            }

            let $layer_label = $action_button.closest('.layers-context-menu').prev();
            let $display_name = $layer_label.find('.display-name').first();
            let $new_layer = $layer_label.parent().next().first()
            var uuid = generate_uuid();
            // Build Modal
            let modal_content = '<div class="form-group">'
                              + '<label class="sr-only" for="new-name-field">New name:</label>'
                              + '<input class="form-control" type="text" id="new-name-field" style="margin-bottom:10px" value="New Layer" autofocus onfocus="this.select();">'
                              + '<label class="sr-only" for="service-type">Map Service Type</label>'
                              + '<select class="form-control" style="margin-bottom:10px" id="service-type">'
                              + '<option value="WMS" selected>WMS</option>'
                              + '</select>'
                              + '<label class="sr-only" for="services-link">Service Link</label>'
                              + '<input class="form-control" type="text" id="services-link" value="https://mrdata.usgs.gov/services/sgmc2" placeholder="Service Link (ex: https://mrdata.usgs.gov/services/sgmc2)" autofocus onfocus="this.select();">'
                              + '<label class="sr-only" for="service-layer-name">Layer Name</label>'
                              + '<input class="form-control" type="text" id="service-layer-name" value="Lithology" placeholder="Layer Name (ex: Lithology)" style="margin-top: 10px" autofocus onfocus="this.select();">'
                              + '</div>';

            let modal = build_action_modal('Add Layer', modal_content, 'Add', 'success');

            // Show Modal
            show_action_modal();

            // Handle Modal Action
            modal.action_button.on('click', function(e) {
                // Rename layer label
                let new_name = modal.content.find('#new-name-field').first().val();
                let service_type = modal.content.find('#service-type').first().val();
                let service_link =  modal.content.find('#services-link').first().val();
                let service_layer_name =  modal.content.find('#service-layer-name').first().val();
                let html_content = '<li class="layer-list-item">'
                html_content += '<label class="flatmark"><span class="display-name">' + new_name + '</span>';
                html_content += '<input type="checkbox" class="layer-visibility-control" checked id="' + uuid + '"';
                html_content += 'data-layer-id="' + uuid + '" data-layer-variable="" name="custom_layers">';
                html_content += '<span class="checkmark checkbox"></span></label>';
                html_content += '<div class="dropdown layers-context-menu pull-right">'
                html_content += '<a id="' + uuid + '--context-menu" class="btn btn-xs dropdown-toggle layers-btn " data-toggle="dropdown" aria-haspopup="true" aria-expanded="true" style="color: rgb(186, 12, 47);">';
                html_content += '<span class="glyphicon glyphicon-option-vertical"></span></a>';
                html_content += '<ul class="dropdown-menu dropdown-menu-right" aria-labeledby="' + uuid + '--context-menu">';
                html_content += '<li><a class="rename-action" href="javascript:void(0);" style="color: rgb(186, 12, 47);"><span class="glyphicon glyphicon-pencil"></span><span class="command-name">Rename</span></a></li>';
                html_content += '<li><a class="remove-action" href="javascript:void(0);" data-remove-type="layer" data-layer-id="' + uuid + '" style="color: rgb(186, 12, 47);"><span class="glyphicon glyphicon-remove"></span><span class="command-name">Remove</span></a></li>';
                html_content += '<div class="form-group">';
                html_content += '<div class="bootstrap-switch bootstrap-switch-wrapper bootstrap-switch-on bootstrap-switch-small bootstrap-switch-animate">'
                html_content += '<div class="bootstrap-switch-container">'
                html_content += '<span class="bootstrap-switch-handle-on bootstrap-switch-success">Public</span><label class="bootstrap-switch-label">&nbsp;</label>'
                html_content += '<span class="bootstrap-switch-handle-off bootstrap-switch-danger">Private</span>'
                html_content += '<input class="form-control bootstrap-switch layer-dropdown-toggle" type="checkbox" data-size="small" data-on-text="Public" data-off-text="Private" data-on-color="success" data-off-color="danger" true>'
                html_content += '</div></div></div>';
                html_content += '<li role="separator" class="divider"></li>';
                html_content += '<li><a class="zoom-to-layer-action" href="javascript:void(0);" data-layer-id="' + uuid + '" style="color: rgb(186, 12, 47);"><span class="glyphicon glyphicon-fullscreen"></span><span class="command-name">Zoom to Layer</span></a></li>';
                html_content += '<li role="separator" class="divider"></li>';
                html_content += '<li>';
                html_content += '<div class="flat-slider-container">';
                html_content += '<label><span class="glyphicon glyphicon-adjust"></span><span class="command-name">Opacity: </span><span class="slider-value">100%</span></label>';
                html_content += '<div class="flat-slider-container">';
                html_content += '<input type="range" class="flat-slider layer-opacity-control" min="0" max="100" value="100" data-layer-id="' + uuid + '" data-layer-variable="">';
                html_content += '</div>';
                html_content += '</li></ul>';
                $new_layer.append(html_content);
                $new_layer.css({'overflow': 'visible'});
                var wms_layers =
                        new ol.layer.Tile({
                            source: new ol.source.TileWMS({
                                url:service_link,
                                params: {'service': service_type, 'version': '1.3.0', 'request': 'GetMap',
                                         'LAYERS': service_layer_name, 'TILED': true},
                                serverType: 'geoserver'
                            })
                        })
                m_layers[uuid] = wms_layers;
                // Hide the modal
                hide_action_modal();
                m_map.addLayer(wms_layers);
                init_layers_tab();

                // Save to resource
                csrf_token = $('input[name=csrfmiddlewaretoken]').val()
                $.ajax({
                    type: 'POST',
                    url: '',
                    data: {'method': 'save_custom_layers',
                           'layer_name': new_name,
                           'uuid': uuid,
                           'service_link': service_link,
                           'service_type': service_type,
                           'service_layer_name': service_layer_name,},
                    beforeSend: xhr => {
                        xhr.setRequestHeader('X-CSRFToken', csrf_token);
                    },
                }).done(function (data) {

                })
                // TODO: Save state to resource - store in attributes?
            });
        });
        // TODO: Implement
        // TODO: Save state to workflow - store in attributes?
    };

    // Properties pop-up
    init_properties_pop_up = function() {
        m_$props_popup_container = $('#properties-popup');
        m_$props_popup_content = $('#properties-popup-content');
        m_$props_popup_closer = $('#properties-popup-close-btn');

        // Create the overlay
        m_props_popup_overlay = new ol.Overlay({
            element: m_$props_popup_container.get(0),
            autoPan: true,
            autoPanAnimation: {
                duration: 250
            }
        });

        m_map.addOverlay(m_props_popup_overlay);

        // Handle closer click events
        m_$props_popup_closer.on('click', function() {
            hide_properties_pop_up();
            TETHYS_MAP_VIEW.clearSelection();
            return false;
        });

        // Unset Display None
        m_$props_popup_container.css('display', 'block');

        // Bind wms select method
        TETHYS_MAP_VIEW.onSelectionChange(on_select_wms_features);

        // Bind vector select methods
        let select_interaction = TETHYS_MAP_VIEW.getSelectInteraction();
        if (select_interaction){
            select_interaction.on('select', on_select_vector_features);
        }
    };

    show_properties_pop_up = function(coordinates) {
        let c = coordinates;

        if (coordinates instanceof ol.geom.Point) {
            c = coordinates.getCoordinates();
        }
        m_props_popup_overlay.setPosition(c);
    };

    hide_properties_pop_up = function() {
        m_props_popup_overlay.setPosition(undefined);
        m_$props_popup_closer.blur();
    };

    reset_properties_pop_up = function() {
        m_$props_popup_content.empty();
        hide_properties_pop_up();
    };

    append_properties_pop_up_content = function(content) {
        m_$props_popup_content.append(content);
    };

    on_select_vector_features = function(event) {
        let selected = event.selected;
        if (selected.length > 0) {
            display_properties(selected);
        }
    };

    on_select_wms_features = function(points_layer, lines_layer, polygons_layer) {
        let layers = [points_layer, lines_layer, polygons_layer];
        display_properties(layers);
    };

    display_properties = function(layers_or_features) {
        let center_points = [];

        // TODO: Add hook to allow apps to customize properties table.

        // Clear popup
        reset_ui(false);

        for (var i = 0; i < layers_or_features.length; i++) {
            let layer_or_features = layers_or_features[i],
                features = [];

            if (layer_or_features && layer_or_features instanceof ol.Feature) {
                features = [layer_or_features];
                center_points.push(compute_center(features));
            }
            else if (layer_or_features && layer_or_features.getSource()
                && layer_or_features.getSource().getFeatures().length) {

                let source = layer_or_features.getSource();
                features = source.getFeatures();
                center_points.push(compute_center(features));
            }
            else {
                continue;
            }

            // Generate one table of properties for each node
            for (var j = 0; j < features.length; j++) {
                let feature = features[j];

                // Generate Title
                let title_markup = generate_properties_table_title(feature);
                append_properties_pop_up_content(title_markup);

                // Generate properties table
                let properties_table = generate_properties_table(feature);
                append_properties_pop_up_content(properties_table);

                // Generate plot button
                let plot_button = generate_plot_button(feature);
                append_properties_pop_up_content(plot_button);
                bind_plot_buttons();

                // Generate plot button
                let action_button = generate_action_button(feature);
                append_properties_pop_up_content(action_button);
                bind_action_buttons();
                // TODO: Add hook to allow apps to customize properties table.
            }
        }

        // Compute popup location
        let popup_location = compute_center(center_points);

        // Show the Popup
        if (popup_location) {
            show_properties_pop_up(popup_location);
        }

        // TODO: Add hook to allow apps to customize properties table.
    };

    reset_ui = function(clear_selection=true) {
        // Clear selection
        if (clear_selection) {
            TETHYS_MAP_VIEW.clearSelection();
        }

        // Reset popup
        reset_properties_pop_up();

        // Hide plot slide sheet
        hide_plot();
    };

    generate_properties_table_title = function(feature) {
        let layer_name = get_layer_name_from_feature(feature);
        let layer = m_layers[layer_name];
        let title = '';

        // Get custom title from layer data properties
        if (layer.hasOwnProperty('tethys_data') && layer.tethys_data.hasOwnProperty('popup_title')) {
            title = layer.tethys_data.popup_title;
        }
        // Or use the legend title as a fallback
        else {
            title = layer.tethys_legend_title;
        }

        let title_markup = '<h6 class="properites-title">' + title + '</h6>';
        return title_markup;
    };

    generate_properties_table = function(feature) {
        let properties = feature.getProperties();
        let geometry = feature.getGeometry();
        let geometry_type = geometry.getType().toLowerCase();
        let feature_class = (('type' in properties) ? properties['type'] : geometry_type);
        let layer_name = get_layer_name_from_feature(feature);
        let layer_data = m_layers[layer_name].tethys_data;
        let excluded_properties = ['geometry', 'the_geom'];
        let extra_table_content = '';

        // Get custom excluded properties
        if (layer_data.hasOwnProperty('excluded_properties')) {
            excluded_properties = excluded_properties.concat(layer_data.excluded_properties);
        }

        // Templates
        let kv_row_template = '<tr><td>{{KEY}}</td><td>{{VALUE}}&nbsp;<span id="{{ELEMENT_CLASS}}-{{PROPERTY}}-units"></span></td></tr>';
        kv_row_template = kv_row_template.replace('{{ELEMENT_CLASS}}', feature_class);
        let table_template = '<table class="table table-condensed table-striped {{CLASS}}">{{ROWS}}</table>';

        // Initial rows
        let rows = '';

        // Append the type of feature
        if (!excluded_properties.includes('type')) {
            rows += kv_row_template
                    .replace('{{KEY}}', 'Type')
                    .replace('{{VALUE}}', geometry.getType())
                    .replace('{{PROPERTY}}', 'type');
        }

        // Build property rows
        for(var property in properties) {
            // Skip excluded properties
            if (in_array(property, excluded_properties)) {
                continue;
            }

            let value = properties[property];

            // If value is an object, build row with appropriate method
            if (value instanceof Object) {
                if (value.hasOwnProperty('type') && value.hasOwnProperty('value') && value.type == 'dataset') {
                    rows += generate_dataset_row(property, value.value);
                } else {
                    console.log('WARNING: Unable to load property row - ' + var_to_title_case(property) + ': ' + value);
                }

            // Otherwise, build simple valued row
            } else {
                // Build row
                rows += kv_row_template
                    .replace('{{KEY}}', var_to_title_case(property))
                    .replace('{{VALUE}}', value)
                    .replace('{{PROPERTY}}', property);
            }

        }

        // Compose table
        if (rows.length) {
            table_template = table_template.replace('{{CLASS}}', feature_class);
            table_template = table_template.replace('{{ROWS}}', rows);
            return table_template;
        }
        else {
            return '';
        }
    };

    generate_dataset_row = function(property, dataset) {
        let dataset_row_template = '<tr><td colspan="2">{{VALUE}}</td></tr>';
        let row = '';
        let dataset_table = '<table class="table">';
        let dataset_table_row_template = '<tr>{{COLUMNS}}</tr>';

        // Get dataset metadata
        let columns = dataset.meta.columns;
        let length = dataset.meta.length;

        // Add dataset title
        row += dataset_row_template.replace('{{VALUE}}', var_to_title_case(property));

        // Add column header row
        let header_columns = '';
        let dataset_table_header_template = '<th>{{VALUE}}</th>';

        $.each(columns, function(index, col) {
            header_columns += dataset_table_header_template.replace('{{VALUE}}', col);
        });

        dataset_table += dataset_table_row_template.replace('{{COLUMNS}}', header_columns);

        // Add value rows
        let value_rows = '';
        let dataset_table_column_template = '<td>{{VALUE}}</td>';

        for (var i = 0; i < length; i++) {
            let row_columns = '';

            $.each(columns, function(index, col) {
                let val = dataset[col][i];
                row_columns += dataset_table_column_template.replace('{{VALUE}}', val);
            });

            value_rows +=  dataset_table_row_template.replace('{{COLUMNS}}', row_columns);
        }

        dataset_table += value_rows;

        // Close out dataset table
        dataset_table += '</table>';
        // Add row containing the dataset table
        row += dataset_row_template.replace('{{VALUE}}', dataset_table);


        return row;
    };

    // Generate UUID
    generate_uuid = function () {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
        });
    }


    // Feature Selection
    init_feature_selection = function() {
        TETHYS_MAP_VIEW.overrideSelectionStyler('points', points_selection_styler);
        TETHYS_MAP_VIEW.overrideSelectionStyler('lines', lines_selection_styler);
        TETHYS_MAP_VIEW.overrideSelectionStyler('polygons', polygons_selection_styler);

        if (m_enable_properties_popup) {
            init_properties_pop_up();
        }
    };

    points_selection_styler = function(feature, resolution) {
        return [new ol.style.Style({
            image: new ol.style.Circle({
                radius: 5,
                fill: new ol.style.Fill({
                    color: SELECTED_POINT_COLOR
                }),
                stroke: new ol.style.Stroke({
                    color: 'white',
                    width: 1
                })
            })
        })];
    };

    lines_selection_styler = function(feature, resolution) {
        return [
            new ol.style.Style({
                stroke: new ol.style.Stroke({
                    color: '#ffffff',
                    width: 6
                })
              }
            ), new ol.style.Style({
                stroke: new ol.style.Stroke({
                    color: SELECTED_LINE_COLOR,
                    width: 4
                })
              }
            )
        ];
    };

    polygons_selection_styler = function(feature, resolution) {
        return [
            new ol.style.Style({
                stroke: new ol.style.Stroke({
                    color: '#ffffff',
                    width: 6
                }),
                fill: new ol.style.Fill({
                    color: 'rgba(115, 0, 229, 0.1)'
                })
              }
            ), new ol.style.Style({
                stroke: new ol.style.Stroke({
                    color: SELECTED_LINE_COLOR,
                    width: 4
                })
              }
            )
        ];
    };

 	// Geocode Methods
    init_geocode = function() {
        if (p_can_geocode) {
            // Add Geocode Control to OpenLayers controls container
            var $geocode_wrapper = $('#map-geocode-wrapper');
            var $overlay_container = $('.ol-overlaycontainer-stopevent');
            $overlay_container.append($geocode_wrapper);

            // Initialize select2 search field
            var $geocoder = $('#geocode_select');
            $geocoder.select2({
                minimumInputLength: 3,
                placeholder: "Search",
                allowClear: true,
                maximumSelectionLength: 1,
                ajax: {
                    url: '.',
                    delay: 2000,
                    type: 'POST',
                    data: function (params) {
                        return {
                            'method': 'find-location-by-query',
                            'q': params.term, // search term
                            'extent': m_extent.join()
                        };
                    },
                    processResults: function (data, params) {
                        m_geocode_objects = data.results;
                        return {
                            results: data.results,
                        };
                    }
                }
            });

            // Bind to on change event
            $geocoder.on('select2:select', do_geocode);
            $geocoder.on('select2:unselect', clear_geocode);
        }
    };

    do_geocode = function(event) {
      // Add classes For styling
      var $search_field = $("li.select2-search.select2-search--inline");
      var i;

      $search_field.addClass("geocode-item-selected");

      // Get the point and add it to the map, also zoom to it's extent
      if (is_defined(m_geocode_objects)) {
          for (i = 0; i < m_geocode_objects.length; i++) {
              if (m_geocode_objects[i].id == $(event.target).val()) {
                  var selected_point = m_geocode_objects[i].point;
                  var selected_bbox = m_geocode_objects[i].bbox;

                  // Add point to the map
                  var geocode_source = new ol.source.Vector({
                      features: [
                          new ol.Feature({
                              geometry: new ol.geom.Point(ol.proj.transform(
                                  selected_point, 'EPSG:4326', 'EPSG:3857'
                              )),
                          }),
                      ],
                  });

                  if (is_defined(m_geocode_layer)) {
                      m_geocode_layer.setSource(geocode_source);
                  } else {
                      // Setup Map Layer
                      var fill = new ol.style.Fill({
                          color: 'rgba(255,0,0,0.9)'
                      });
                      var stroke = new ol.style.Stroke({
                          color: 'rgba(255,255,255,1)',
                          width: 2
                      });
                      var geocode_style = new ol.style.Style({
                          image: new ol.style.Circle({
                              fill: fill,
                              stroke: stroke,
                              radius: 8
                          }),
                          fill: fill,
                          stroke: stroke
                      });

                      m_geocode_layer = new ol.layer.Vector({
                          source: geocode_source,
                          style: geocode_style
                      });

                      m_map.addLayer(m_geocode_layer);
                  }

                  // Zoom to the bounding box provided
                  TETHYS_MAP_VIEW.zoomToExtent(selected_bbox);
              }
          }
      } else {
          console.error("No Geocode objects defined.")
      }
    };

    clear_geocode = function(event) {
        // Remove classes For styling
        var $search_field = $("li.select2-search.select2-search--inline");
        $search_field.removeClass("geocode-item-selected");

        // Clear the map
        if (is_defined(m_geocode_layer)) {
          var source = m_geocode_layer.getSource();
          var features = source.getFeatures();
          if (features != null && features.length > 0) {
             for (var x in features) {
                source.removeFeature(features[x]);
             }
          }
        }
    };

    // Cache methods
    add_to_cache = function(cache, key, obj) {
        cache[key] = obj;
    };

    get_from_cache = function(cache, key) {
        if (is_in_cache(cache, key)) {
            return cache[key];
        }
    };

    is_in_cache = function(cache, key) {
        if (key in cache) {
            return true;
        }
        else {
            return false;
        }
    };

    remove_from_cache = function(cache, key) {
        if (is_in_cache(cache, key)) {
            delete cache[key];
        }
    };

    // Drawing methods
    init_draw_controls = function() {
        var left_position = 7,
            LEFT_POSITION_OFFSET = 42;
        $('.tethys-map-view-draw-control').each(function(index, control) {
            // Reset position of draw controls so they are left aligned on the bottom.
            $(control).css('left', left_position + 'px');
            $(control).css('bottom', '7px');
            $(control).css('top', 'auto');
            left_position += LEFT_POSITION_OFFSET;
        });

        // Reset tooltips to show on top
        $('[data-toggle="tooltip"]').tooltip('destroy');
        $('[data-toggle="tooltip"]').tooltip({'placement': 'top'});
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
	m_public_interface = {
	    /*
	     * Override the default properties table generator
	     */
	    properties_table_generator: function(f) {
	        generate_properties_table = f;
	    },

	    action_button_generator: function(f) {
	        generate_action_button = f;
	    },

	    plot_button_generator: function(f) {
	        generate_plot_button = f;
	    },

	    plot_loader: function(f) {
	        load_plot = f;
	    },

	    action_loader: function(f) {
	        load_action = f;
	    },

        get_layer_name_from_feature: get_layer_name_from_feature,
        get_feature_id_from_feature: get_feature_id_from_feature,
	};

	/************************************************************************
 	*                  INITIALIZATION / CONSTRUCTOR
 	*************************************************************************/

	// Initialization: jQuery function that gets called when
	// the DOM tree finishes loading
	$(function() {
	    // Load config
	    parse_permissions();
	    parse_attributes();

	    // Setup
	    setup_ajax();
	    setup_map();

		// Initialize
		init_layers_tab();
        init_geocode();
        init_plot();
        init_draw_controls();
	});

	return m_public_interface;

}()); // End of package wrapper
// NOTE: that the call operator (open-closed parenthesis) is used to invoke the library wrapper
// function immediately after being parsed.