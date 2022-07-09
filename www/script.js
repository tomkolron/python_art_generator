function gen() {
  var size = $('.size').val();
  var line_amount = $('.line_amount').val();
  var line_width = $('.line_width').val();
  var padding = $('.padding').val();
  var type = 2;
  var border_width = $('.border_width').val();
  eel.gen_art(size, line_amount, line_width, padding, type, border_width)(function (ret) {
    console.log(ret);
    $('img').attr('src', ret);
  })
}

$( document ).ready(function() {
  $('.size').on('input', function () {
    $('.size_wrap > p').text($(this).val());
  });
});
