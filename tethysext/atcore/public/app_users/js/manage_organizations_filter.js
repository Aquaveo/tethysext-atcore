/**
 * Instant client-side filter for the manage_organizations card list.
 *
 * The organizations page is a list of collapsible cards grouped by license rather than a table,
 * so jQuery DataTables does not apply. This filters the rendered cards by organization name as the
 * user types: non-matching cards are hidden, license groups with no visible cards are hidden, and a
 * "no results" message is shown when nothing matches. Each card carries its searchable text in a
 * data-search attribute (set in the template).
 */
(function () {
    document.addEventListener('DOMContentLoaded', function () {
        var input = document.getElementById('organization-search-input');
        var clear = document.getElementById('organization-search-clear');
        var noResults = document.getElementById('organization-no-results');
        var info = document.getElementById('organization-info');

        if (!input) {
            return;
        }

        var total = document.querySelectorAll('.manage-card').length;
        var labelPlural = (info && info.getAttribute('data-label')) || 'entries';
        var labelSingular = (info && info.getAttribute('data-label-singular')) || labelPlural;

        function label(count) {
            return count === 1 ? labelSingular : labelPlural;
        }

        function updateInfo(matched, isFiltered) {
            if (!info) {
                return;
            }
            if (isFiltered) {
                info.textContent = 'Showing ' + matched + ' ' + label(matched) +
                    ' (filtered from ' + total + ' total)';
            } else {
                info.textContent = 'Showing ' + total + ' ' + label(total);
            }
        }

        function applyFilter() {
            var term = input.value.trim().toLowerCase();
            var isFiltered = term.length > 0;

            if (clear) {
                clear.classList.toggle('d-none', !isFiltered);
            }

            var matched = 0;

            document.querySelectorAll('.organization-license-group').forEach(function (group) {
                var groupHasMatch = false;

                group.querySelectorAll('.manage-card').forEach(function (card) {
                    var haystack = (card.getAttribute('data-search') || '').toLowerCase();
                    var match = term === '' || haystack.indexOf(term) > -1;
                    card.classList.toggle('d-none', !match);
                    if (match) {
                        groupHasMatch = true;
                        matched += 1;
                    }
                });

                // Hide a license group heading when none of its cards match.
                group.classList.toggle('d-none', !groupHasMatch);
            });

            if (noResults) {
                noResults.classList.toggle('d-none', matched > 0);
            }

            updateInfo(matched, isFiltered);
        }

        input.addEventListener('keyup', applyFilter);

        if (clear) {
            clear.addEventListener('click', function () {
                input.value = '';
                applyFilter();
                input.focus();
            });
        }

        // Populate the count on load.
        applyFilter();
    });
})();
