function files_tab_loaded() {
    var hierarchy = document.getElementById("hierarchy");
    hierarchy.addEventListener("click", function(event){
        var elem = event.target;
        if(elem.tagName.toLowerCase() == "span" && elem !== event.currentTarget)
        {
            var type = elem.classList.contains("folder") ? "folder" : "file";
            if(type=="folder")
            {
                var isexpanded = elem.dataset.isexpanded=="true";
                if(isexpanded)
                {
                    elem.classList.remove("glyphicon-folder-open");
                    elem.classList.add("glyphicon-folder-close");
                }
                else
                {
                    elem.classList.remove("glyphicon-folder-close");
                    elem.classList.add("glyphicon-folder-open");
                }
                elem.dataset.isexpanded = !isexpanded;

                path_input = document.getElementById("filepath_input")
                path_input.placeholder = elem.dataset.filepath

                var toggleelems = [].slice.call(elem.parentElement.children);
                var classnames = "file,foldercontainer,noitems".split(",");

                var elem_slug = elem.dataset.slug;
                viewport_items = document.getElementsByClassName("viewport_item");
                for (var i = 0; i < viewport_items.length; i++) {
                    viewport_item = viewport_items.item(i);
                    viewport_item.style.visibility = viewport_item.dataset.parentslug == elem_slug ? "visible":"collapse";
                }

                toggleelems.forEach(function(element){
                    if(classnames.some(function(val){return element.classList.contains(val);}))
                    element.style.display = isexpanded ? "none":"block";
                });
            }
        }
    });
}