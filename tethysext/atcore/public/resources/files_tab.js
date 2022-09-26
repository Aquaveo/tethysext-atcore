// A function to hide and show the files in the viewport based on which item is selected.
function show_hide_files(slug, path) {
    // Get all viewport items and turn them on or off if they match the slug.
    viewport_items = document.getElementsByClassName("viewport_item");
    for (var i = 0; i < viewport_items.length; i++) {
        viewport_item = viewport_items.item(i);
        viewport_item.style.visibility = viewport_item.dataset.parentslug == slug ? "visible":"collapse";
    }
    // Update the path text field to show the current path being viewed.
    path_input = document.getElementById("filepath_input")
    path_input.placeholder = path;
}

// A function to change the isselected data when a tree item is selected.
function change_tree_selection(selected_elem) {
    // Take the is selected data off of all tree elements
    document.querySelectorAll('.folder').forEach(function(elem){
        elem.dataset.isselected = "false";
    });
    // Add the selected data back to the tree element being selected.
    selected_elem.dataset.isselected="true";
}

// A function used to collapse or expand tree item and change their glyph.
function collapse_tree_elements(elem) {
    var toggleelems = [].slice.call(elem.parentElement.children);
    var classnames = "file,foldercontainer,noitems".split(",");
    var isexpanded = elem.dataset.isexpanded=="true";
    // Change the glyphicon for the folder based on if it is expanded.
    if(!isexpanded)
    {
        elem.classList.remove("bi-folder2-open");
        elem.classList.add("bi-folder2");
    }
    else
    {
        elem.classList.remove("bi-folder2");
        elem.classList.add("bi-folder2-open");
    }
    // Hide or show each tree item based on if it is expanded or not.
    toggleelems.forEach(function(element){
        if(classnames.some(function(val){return element.classList.contains(val);}))
        element.style.display = isexpanded ? "block":"none";
    });
}

// A function to change the viewport shown files after a tree item is selected.
function change_view_after_tree_selection(elem, do_collapse) {
    if(elem.tagName.toLowerCase() == "span" && elem !== event.currentTarget)
    {
        var type = elem.classList.contains("folder") ? "folder" : "file";
        if(type=="folder")
        {
            // Get the path, and slug for the element in the tree and update the viewport.
            var elem_slug = elem.dataset.slug;
            var elem_path = elem.dataset.filepath;
            show_hide_files(elem_slug, elem_path);

            // Expand or collapse the tree item if do_collapse is true.
            if (do_collapse) {
                var isexpanded = elem.dataset.isexpanded=="true";
                elem.dataset.isexpanded = !isexpanded;
                collapse_tree_elements(elem);
            }
        }
    }
}

// Callback that performs post load actions for workflows tab
function files_tab_loaded() {

    // Add the collapse and expand functionality to the tree view.
    var hierarchy = document.getElementById("hierarchy");
    // A single click should just show the files and highlight.
    hierarchy.addEventListener("click", function(event){
        var elem = event.target;
        change_tree_selection(elem);
        change_view_after_tree_selection(elem, false);
        document.getElementById('up_button').dataset.slug = elem.dataset.parentslug != "None" ? elem.dataset.parentslug:elem.dataset.slug;
        document.getElementById('up_button').dataset.filepath = elem.dataset.parentpath;
    });
    // A double click should expand or collapse an item in the tree.
    hierarchy.addEventListener("dblclick", function(event){
        var elem = event.target;
        change_tree_selection(elem);
        change_view_after_tree_selection(elem, true);
    });

    // Add functionality for double clicking on a folder in the viewport.
    document.querySelectorAll('.viewport_dir').forEach(function(row) {
        $(row).bind("dblclick", function(){
            show_hide_files(row.dataset.slug, row.dataset.filepath);
            document.querySelectorAll('.folder').forEach(function(elem) {
                if (row.dataset.slug == elem.dataset.slug) {
                    change_tree_selection(elem);
                }
                if (row.dataset.parentslug == elem.dataset.slug) {
                    elem.dataset.isexpanded = true;
                }
                collapse_tree_elements(elem);
            });

            document.getElementById('up_button').dataset.slug = row.dataset.parentslug;
            document.getElementById('up_button').dataset.filepath = row.dataset.parentpath;
        });
    });

    // Collapse all items in the tree.
    document.getElementById('tree-collapse').addEventListener("click", function() {
        document.querySelectorAll('.folder').forEach(function(folder) {
                folder.dataset.isexpanded = false;
                folder.classList.remove("bi-folder2-open");
                folder.classList.add("bi-folder2");
                collapse_tree_elements(folder);
        });
    });
    // Expand all items in the tree.
    document.getElementById('tree-expand').addEventListener("click", function() {
        document.querySelectorAll('.folder').forEach(function(folder) {
                folder.dataset.isexpanded = true;
                folder.classList.remove("bi-folder2");
                folder.classList.add("bi-folder2-open");
                collapse_tree_elements(folder);
        });
    });

    document.querySelectorAll('.viewport_file').forEach(function(row) {
        $(row).bind("dblclick", function(){
            var download_url = window.location + '?tab_action=download_file&file-path='
                + row.dataset.filepath + '&collection-id=' + row.dataset.collectionid
            var redirectWindow = window.open(download_url,  '_blank');
            redirectWindow.location;

        });
    });

    // Up Button Handler
    $('#up_button').bind('click', function() {
        button = document.getElementById('up_button');
        var slug = button.dataset.slug;
        if (slug != "None") {
            show_hide_files(button.dataset.slug, button.dataset.filepath);
            document.querySelectorAll('.folder').forEach(function(elem) {
                if (slug == elem.dataset.slug) {
                    change_tree_selection(elem);
                    button.dataset.slug = elem.dataset.parentslug;
                    button.dataset.filepath = elem.dataset.parentpath;
                }
            });
        }
    });

    document.querySelectorAll('.folder').forEach(function(elem){
        collapse_tree_elements(elem);
    });

    data_table = $('#viewport-table').DataTable({
        "paging":   false,
        "searching":   false,
        "info":     false,
        "order": [[0, "asc"]]
    });
}