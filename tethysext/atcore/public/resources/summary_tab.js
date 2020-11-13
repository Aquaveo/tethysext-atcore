// Callback that loads the summary image after loading the rest of the summary tab
function summary_tab_loaded() {
    $('.map-preview').load('?tab-action=load-summary-tab-preview-image');
}