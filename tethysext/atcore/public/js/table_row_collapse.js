document.addEventListener('DOMContentLoaded', function() {
    let expandToggles = document.querySelectorAll('[data-ts-toggle="table-row-collapse"]');
    expandToggles.forEach(function(toggle, _) {
        let targets = document.querySelectorAll(toggle.dataset.tsTarget);
        toggle.addEventListener('click', function() {
            // Hide the child rows
            targets.forEach(function(target, _) {
                target.classList.toggle('d-none');
            });

            // Rotate toggle button icon
            toggle.classList.toggle('expanded');
        });
    });

    let expandAllToggles = document.querySelectorAll('[data-ts-toggle="table-row-expand-all"]');
    expandAllToggles.forEach(function(toggle, _) {
        toggle.addEventListener('click', function() {
            let expandToggles = document.querySelectorAll('[data-ts-toggle="table-row-collapse"]');
            expandToggles.forEach(function(t, _) {
                let targets = document.querySelectorAll(t.dataset.tsTarget);
                targets.forEach(function(target, _) {
                    target.classList.remove('d-none');
                });

                t.classList.add('expanded');
            });
        });
    });

    let collapseAllToggles = document.querySelectorAll('[data-ts-toggle="table-row-collapse-all"]');
    collapseAllToggles.forEach(function(toggle, _) {
        toggle.addEventListener('click', function() {
            let expandToggles = document.querySelectorAll('[data-ts-toggle="table-row-collapse"]');
            expandToggles.forEach(function(t, _) {
                let targets = document.querySelectorAll(t.dataset.tsTarget);
                targets.forEach(function(target, _) {
                    target.classList.add('d-none');
                });

                t.classList.remove('expanded');
            });
        });
    });
});