document.addEventListener('DOMContentLoaded', function() {
    let collapseToggles = document.querySelectorAll('[data-ts-toggle="table-row-collapse"]');
    collapseToggles.forEach(function(toggle, _) {
        let targets = document.querySelectorAll(toggle.dataset.tsTarget);
        toggle.addEventListener('click', function() {
            // Hide the child rows
            targets.forEach(function(target, _) {
                target.classList.toggle('d-none');
            });

            // Rotate toggle button icon
            toggle.classList.toggle('rotate-90');
        });
    });
});