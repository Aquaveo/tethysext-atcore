/*****************************************************************************
 * FILE:    lazy_load_tabs.js
 * DATE:    August 8, 2018
 * AUTHOR:  nswain
 * COPYRIGHT: (c) Aquaveo 2018
 *****************************************************************************/

/*****************************************************************************
 *                      LIBRARY WRAPPER
 *****************************************************************************/

let LAZY_LOAD_TABS = (function() {
    // Wrap the library in a package function
    "use strict"; // And enable strict mode for this library

    /************************************************************************
    *                      MODULE LEVEL / GLOBAL VARIABLES
    *************************************************************************/
 	  // Constants
    let m_loaded_tabs,
        m_resource_id,
        m_active_tab,
        m_default_tab,
        m_tab_page_url_template,
        m_get_tab_url_template,
        m_public_interface;  // Object returned by the module


    /************************************************************************
    *                    PRIVATE FUNCTION DECLARATIONS
    *************************************************************************/
    let load_tab, tab_is_loaded, trigger_tab_change, set_url_to_tab, restore_tab_from_url, get_tab_name_from_tab,
        get_tab_content_from_tab;

    /************************************************************************
    *                    PRIVATE FUNCTION IMPLEMENTATIONS
    *************************************************************************/
    get_tab_name_from_tab = function(tab) {
        let tab_content = get_tab_content_from_tab(tab);
        let tab_name = tab_content.replace('#', '').toLowerCase();
        return tab_name;
    }

    get_tab_content_from_tab = function(tab) {
        let a = $(tab).children('a').first();
        let tab_content = $(a).attr('href');
        return tab_content;
    }

    load_tab = function() {
        let that = this;
        let tab_content = get_tab_content_from_tab(this);
        let tab_name = get_tab_name_from_tab(this);

        set_url_to_tab(tab_name);

        // Skip load if tab is already loaded
        if (tab_is_loaded(tab_name)) { return; }

        let tab_url = '?tab_action=default';

        $(tab_content).load(tab_url, function() {
            let callback = $(that).attr('data-callback');
            if (callback) {
                try {
                  window[callback]();
                } catch(err) {
                  console.log(`Error: Unable to find callback "${callback}".`);
                }
            }
        });

        m_loaded_tabs.push(tab_name);
    };

    tab_is_loaded = function(tab_name) {
        return (m_loaded_tabs.indexOf(tab_name) >= 0);
    }

    set_url_to_tab = function (tab, reload) {
        let url = window.location.href;
        let old_path = window.location.pathname;
        let new_path = old_path.replace(m_active_tab, tab);
        m_active_tab = tab;

        let state = null;
        if (old_path !== new_path) {
            url = url.replace(old_path, new_path);
            if (reload) {
                window.location = url;
            } else {
                window.history.pushState(state, null, url);
            }
        } else {
            window.history.replaceState(state, null, url);
        }
    };

    restore_tab_from_url = function (e) {
        if (m_active_tab) {
            $('a[href="#' + m_active_tab + '"]').trigger('click');
        } else {
            $('a[href="#' + m_default_tab + '"]').trigger('click');
        }
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
    $(document).ready(function() {
        // Cache the js scripts that are fetched for tabs
        $.ajaxSetup({
          cache: true
        });

        // Parse project detail page attributes
        let cur_active = $(".lazy-load-tab.active");
        let config = $("#lazy-load-config");
        // Derive default tab from active class or first
        let default_tab = cur_active.length ? cur_active : $(".lazy-load-tab").first();
        m_default_tab = get_tab_name_from_tab(default_tab);
        m_active_tab = config.attr('data-active-tab');
        m_loaded_tabs = [];

        // Bind tab loading
        $('.lazy-load-tab').on('click', load_tab);
        $(window).on('popstate', restore_tab_from_url);

        restore_tab_from_url();

    });

    return m_public_interface;

}()); // End of package wrapper
// NOTE: that the call operator (open-closed parenthesis) is used to invoke the library wrapper
// function immediately after being parsed.