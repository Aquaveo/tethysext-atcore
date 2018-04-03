$(function() {
  $('.spinner .btn:first-of-type').on('click', function() {
    var parent = $(this).closest('.input-group.spinner'),
        input = $(parent).children('input').first(),
        increment = parseInt($(input).attr('data-spinner-increment'), 10),
        max = parseInt($(input).attr('data-spinner-max'), 10),
        incremented_val;

    if (!isNaN(increment)) {
        incremented_val = parseInt($(input).val()) + increment;
    } else {
        incremented_val = parseInt($(input).val()) + 1;
    }

    // Check maximum constraint
    if (max && incremented_val > max)
    {
      return;
    }

    // Set value and trigger change event
    $(input).val(incremented_val);
    $(input).trigger('change');
  });

  $('.spinner .btn:last-of-type').on('click', function() {
    var parent = $(this).closest('.input-group.spinner'),
        input = $(parent).children('input').first(),
        increment = parseInt($(input).attr('data-spinner-increment'), 10),
        min = parseInt($(input).attr('data-spinner-min'), 10),
        incremented_val;

    if (!isNaN(increment)) {
        incremented_val = parseInt($(input).val()) + increment;
    } else {
        incremented_val = parseInt($(input).val()) - 1;
    }

    // Check minimum constraint
    if (min && incremented_val < min)
    {
      return;
    }

    // Set value and trigger change event
    $(input).val(incremented_val);
    $(input).trigger('change');
  });

  // Validate spinner value
  $('.spinner input').on('keypress', function(e) {
    var min = parseInt($(this).attr('data-spinner-min')),
        max = parseInt($(this).attr('data-spinner-max')),
        value = parseInt($(this).val());

    if (!/^[0-9\-]+$/.test(e.key))
    {
      e.preventDefault();
    }
  });

  $('.spinner input').on('input', function(e) {
    var min = parseInt($(this).attr('data-spinner-min')),
        max = parseInt($(this).attr('data-spinner-max')),
        value = parseInt($(this).val());

    if (min && value && value < min)
    {
      $(this).val(min);
      $(this).trigger('change');
    }
    else if (max && value && value > max)
    {
      $(this).val(max);
      $(this).trigger('change');
    }
  });

  $('.spinner input').on('change', function(e) {
    var min = parseInt($(this).attr('data-spinner-min')),
        value = parseInt($(this).val());
    if (isNaN(value))
    {
      $(this).val((min && min < 0) ? 0 : min);
      $(this).trigger('change');
    }
  });
});