function show_hide_files(slug, path) {
    viewport_items = document.getElementsByClassName("viewport_item");
    for (var i = 0; i < viewport_items.length; i++) {
        viewport_item = viewport_items.item(i);
        viewport_item.style.visibility = viewport_item.dataset.parentslug == slug ? "visible":"collapse";
    }
    path_input = document.getElementById("filepath_input")
    path_input.placeholder = path;
}

function change_tree_selection(selected_elem) {
    document.querySelectorAll('.folder').forEach(function(elem){
        elem.dataset.isselected = "false";
    });
    selected_elem.dataset.isselected="true";
}

function collapse_tree_elements(elem) {
    var toggleelems = [].slice.call(elem.parentElement.children);
    var classnames = "file,foldercontainer,noitems".split(",");
    var isexpanded = elem.dataset.isexpanded=="true";
    if(!isexpanded)
    {
        elem.classList.remove("glyphicon-folder-open");
        elem.classList.add("glyphicon-folder-close");
    }
    else
    {
        elem.classList.remove("glyphicon-folder-close");
        elem.classList.add("glyphicon-folder-open");
    }
    toggleelems.forEach(function(element){
        if(classnames.some(function(val){return element.classList.contains(val);}))
        element.style.display = isexpanded ? "block":"none";
    });
}

function change_view_after_tree_selection(elem, do_collapse) {
    if(elem.tagName.toLowerCase() == "span" && elem !== event.currentTarget)
    {
        var type = elem.classList.contains("folder") ? "folder" : "file";
        if(type=="folder")
        {
            var elem_slug = elem.dataset.slug;
            var elem_path = elem.dataset.filepath;
            show_hide_files(elem_slug, elem_path);

            if (do_collapse) {
                var isexpanded = elem.dataset.isexpanded=="true";
                elem.dataset.isexpanded = !isexpanded;
                collapse_tree_elements(elem);
            }
        }
    }
}

function files_tab_loaded() {
    var hierarchy = document.getElementById("hierarchy");
    hierarchy.addEventListener("click", function(event){
        var elem = event.target;
        change_tree_selection(elem);
        change_view_after_tree_selection(elem, false);
    });
    hierarchy.addEventListener("dblclick", function(event){
        var elem = event.target;
        change_tree_selection(elem);
        change_view_after_tree_selection(elem, true);
    });

    document.querySelectorAll('.viewport_dir').forEach(function(row) {
        $(row).bind("dblclick", function(){
            show_hide_files(row.dataset.slug, row.dataset.filepath);
            document.querySelectorAll('.folder').forEach(function(elem) {
                if (row.dataset.slug == elem.dataset.slug) {
                    change_tree_selection(elem);
                }
            });
        });
    });

    document.querySelectorAll('.viewport_file').forEach(function(row) {
        $(row).bind("dblclick", function(){
            alert("Download file: " + row.dataset.filepath);
        });
    });

    document.querySelectorAll('.folder').forEach(function(elem){
        collapse_tree_elements(elem);
    });
}