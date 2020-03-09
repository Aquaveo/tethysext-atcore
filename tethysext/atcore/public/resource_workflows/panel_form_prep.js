$(function() {
   $('#workflow-form').on('submit', function(e) {
       // Add names to select boxes
       $('#workflow-form .bk-input-group select').each(function() {
           $(this).attr('name', 'param-form-' + $(this).prev('label').text().toLowerCase().replace(' ', '_'));
       });
       // Add names to input boxes
       $('#workflow-form .bk-input-group input').each(function() {
           $(this).attr('name', 'param-form-' + $(this).prev('label').text().toLowerCase().replace(' ', '_'));
       });
   });
});