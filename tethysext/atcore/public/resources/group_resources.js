function get_selected_resources() {
    let checked_controls = document.querySelectorAll(".select-resource-control:checked");
    let resources = Array.from(checked_controls).map(ctl => { 
        return {id: ctl.dataset.id, name: ctl.dataset.name};
    });
    return resources;
}

document.addEventListener('DOMContentLoaded', function() {
    let new_from_selected_button = document.getElementById("btn-group-resource");
    new_from_selected_button.addEventListener("click", function(event) {
        let resources = get_selected_resources();
    
        // Remove all select options
        for (const option of [...document.querySelectorAll('#new-group-resources-select option')]) {
            option.remove();
        }
    
        // Add select options from selected resources
        let resources_select = document.getElementById('new-group-resources-select');
        resources.forEach((resource, idx) => {
            resources_select.options.add(new Option(resource.name, resource.id, true, true));
        });
    
        // Show the modal
        let modal = new bootstrap.Modal(document.getElementById('new-group-modal'));
        modal.show();
    });

    let modal_new_group_button = document.getElementById("modal-new-group-button");
    modal_new_group_button.addEventListener("click", function(event) {
        // Show loading dots
        document.querySelector('#new-group-modal .modal-footer')
          .innerHTML = '<img src="/static/atcore/images/loading-dots-small.gif">';
    
        // Get form data
        let new_from_selected_form = document.getElementById('new-group-form');
        let form_data = new FormData(new_from_selected_form);
    
        // Send POST request
        fetch('', {
            method: 'POST',
            body: form_data,
            credentials: 'same-origin',
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.onbeforeunload = null;
                location.reload();
            } else {
                console.error(data);
                TETHYS_APP_BASE.alert("danger", "An unexpected error has occurred. Please try again.");
            }
        });
    });
}, false);
