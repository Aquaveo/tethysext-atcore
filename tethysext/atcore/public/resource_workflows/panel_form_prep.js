$(function() {
   $('#workflow-form').on('submit', function(e) {
       console.warn('WARNING: Values will only be submitted for the following widgets: select, input, and slider.');
       // Add names to select boxes
       $('#workflow-form .bk-input-group select').each(function() {
           $(this).attr('name', 'param-form-' + $(this).prev('label').text().toLowerCase().split(' ').join('_'));
       });
       // Add names to input boxes
       $('#workflow-form .bk-input-group input').each(function() {
           $(this).attr('name', 'param-form-' + $(this).prev('label').text().toLowerCase().split(' ').join('_'));
       });
       // Add names to slider widgets
       $('#workflow-form .bk-input-group .bk-slider-title').each(function() {
           // e.g.: "Wave length: 11.1" -> ["Some widget", "11.1"]
           [slider_title, slider_value] = $(this).text().split(': ');
           // e.g.: "Some widget" -> "param-form-some_widget"
           let slider_name = `param-form-${slider_title.toLowerCase().split(' ').join('_')}`;
           // Insert a new input field b/c the slider widgets don't have an input associated with them.
           $(this).after(`<input hidden name=${slider_name} value=${slider_value}>`);
       });
   });
});