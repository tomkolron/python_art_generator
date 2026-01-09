var selectedStateId = null;
var selectedImageSrc = null;

function gen() {
  $('.imgs_wrap').empty();
  var size = $('.size').val();
  var line_amount = $('.line_amount').val();
  var line_width = $('.line_width').val();
  var line_width_variation = $('.line_width_variation').val();
  var padding = $('.padding').val();
  var border_width = $('.border_width').val();
  for(let i = 0; i < 9; i++) {
    eel.generate_art(size, line_amount, line_width, line_width_variation, padding, border_width)(function (ret) {
      var img = $('<img>').attr('src', ret.image);
      if (ret.state_id) {
        img.attr('data-state-id', ret.state_id);
        img.attr('data-image-src', ret.image);
        img.on('click', function() {
          // Remove previous selection
          $('.imgs_wrap img').removeClass('selected');
          // Select this image
          $(this).addClass('selected');
          selectedStateId = $(this).attr('data-state-id');
          selectedImageSrc = $(this).attr('data-image-src');
          // Show selected image in preview
          $('#selected-image-container').html('<img src="' + selectedImageSrc + '">');
          $('#video-section').slideDown(300);
          // Scroll to video section
          $('html, body').animate({
            scrollTop: $('#video-section').offset().top - 20
          }, 500);
        });
      }
      $('.imgs_wrap').prepend(img);
    })
  }
}

function generateVideo() {
  if (!selectedStateId) {
    alert('Please select an art piece first by clicking on it.');
    return;
  }
  
  var video_speed = parseFloat($('.video_speed').val());
  var video_zoom = parseFloat($('.video_zoom').val());
  var video_zoom_speed = parseFloat($('.video_zoom_speed').val());
  var end_line_amount = $('.end_line_amount').val();
  var end_line_width = $('.end_line_width').val();
  var end_line_width_variation = $('.end_line_width_variation').val();
  var end_padding = $('.end_padding').val();
  var end_border_width = $('.end_border_width').val();
  
  var displaySpeed = (parseFloat(video_speed) / 20.0).toFixed(1);
  $('#video-status').html('<p>🎬 Generating video (300 frames at 10fps, speed: ' + displaySpeed + 'x, zoom: ' + video_zoom + 'x)... This should take 30-60 seconds. Please wait...</p>');
  $('#video-container').html('<div style="color: white; text-align: center; padding: 50px;">Generating...</div>');
  
  eel.generate_video(selectedStateId, video_speed, video_zoom, video_zoom_speed, end_line_amount, end_line_width, 
                     end_line_width_variation, end_padding, end_border_width)(function (ret) {
    if (ret.error) {
      $('#video-status').html('<p style="color: #e74c3c;">❌ Error: ' + ret.error + '</p>');
      $('#video-container').html('<div style="color: white; text-align: center; padding: 50px;">Error generating video</div>');
    } else if (ret.video) {
      $('#video-status').html('<p style="color: #27ae60;">✅ Video generated successfully!</p>');
      var video = $('<video>').attr('src', ret.video)
                              .attr('controls', true)
                              .attr('autoplay', true)
                              .attr('loop', true);
      $('#video-container').html(video);
    }
  });
}

var isPreviewRunning = false;
var previewInterval = null;
var previewTimeFactor = 0.0;
var previewStartTime = null;
var gyroX = 0.0;
var gyroY = 0.0;
var isJoystickDragging = false;

function toggleRealtimePreview() {
  if (!selectedStateId) {
    alert('Please select an art piece first by clicking on it.');
    return;
  }
  
  if (isPreviewRunning) {
    stopRealtimePreview();
  } else {
    startRealtimePreview();
  }
}

function startRealtimePreview() {
  isPreviewRunning = true;
  previewStartTime = Date.now();
  $('#preview-toggle-btn').text('Stop Preview').removeClass('btn-primary').addClass('btn-danger');
  $('#realtime-preview-container').show();
  $('#preview-status').text('Preview running... Adjust parameters to see changes in real-time!');
  
  var canvas = document.getElementById('realtime-canvas');
  if (!canvas) {
    $('#realtime-preview-container').html('<canvas id="realtime-canvas" style="max-width: 100%; border-radius: 12px; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); background: #000;"></canvas>');
    canvas = document.getElementById('realtime-canvas');
  }
  
  // Set canvas size
  var previewSize = 800;
  canvas.width = previewSize;
  canvas.height = previewSize;
  
  // Start generating frames
  generatePreviewFrame();
}

function stopRealtimePreview() {
  isPreviewRunning = false;
  if (previewInterval) {
    clearInterval(previewInterval);
    previewInterval = null;
  }
  $('#preview-toggle-btn').text('Start Real-Time Preview').removeClass('btn-danger').addClass('btn-primary');
  $('#preview-status').text('Preview stopped.');
}

function generatePreviewFrame() {
  if (!isPreviewRunning || !selectedStateId) {
    stopRealtimePreview();
    return;
  }
  
  // Calculate time factor (continuous, never resets)
  // Use elapsed time directly, scaled to create smooth continuous animation
  // The modulo ensures it stays in 0-1 range but with a very long cycle
  var elapsed = (Date.now() - previewStartTime) / 1000.0; // seconds
  // Use modulo with a very large number so it effectively never resets in practice
  // This creates a continuous animation that doesn't loop noticeably
  previewTimeFactor = (elapsed * 0.01) % 1.0; // Slow progression, very long cycle
  
  // Get current parameter values
  var video_speed = parseFloat($('.video_speed').val());
  var video_zoom = parseFloat($('.video_zoom').val());
  var video_zoom_speed = parseFloat($('.video_zoom_speed').val());
  var gyro_x = gyroX; // Use joystick value
  var gyro_y = gyroY; // Use joystick value
  var end_line_amount = $('.end_line_amount').val();
  var end_line_width = $('.end_line_width').val();
  var end_line_width_variation = $('.end_line_width_variation').val();
  var end_padding = $('.end_padding').val();
  var end_border_width = $('.end_border_width').val();
  
  // Request frame
  eel.generate_realtime_frame(selectedStateId, previewTimeFactor, video_speed, video_zoom, video_zoom_speed,
                              gyro_x, gyro_y, end_line_amount, end_line_width, end_line_width_variation, end_padding, end_border_width)(
    function (ret) {
      if (ret.error) {
        $('#preview-status').html('<span style="color: red;">Error: ' + ret.error + '</span>');
        stopRealtimePreview();
      } else if (ret.frame) {
        // Display frame on canvas
        var canvas = document.getElementById('realtime-canvas');
        var ctx = canvas.getContext('2d');
        var img = new Image();
        img.onload = function() {
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
          
          // Schedule next frame (target ~15 fps for smooth preview)
          if (isPreviewRunning) {
            setTimeout(generatePreviewFrame, 1000 / 15); // ~15 fps
          }
        };
        img.src = ret.frame;
      }
    }
  );
}

$( document ).ready(function() {
  $('.size').on('input', function () {
    $('.size_label').text($(this).val());
  });
  $('.video_speed').on('input', function () {
    var speed = parseFloat($(this).val());
    var displaySpeed = (speed / 20.0).toFixed(1); // Convert to display scale (20x = 1.0x)
    $('.video_speed_label').text(displaySpeed + 'x');
    // Update preview if running
    if (isPreviewRunning) {
      // Preview will update on next frame
    }
  });
  $('.video_zoom').on('input', function () {
    var zoom = parseFloat($(this).val());
    $('.video_zoom_label').text(zoom.toFixed(2) + 'x');
  });
  $('.video_zoom_speed').on('input', function () {
    var zoomSpeed = parseFloat($(this).val());
    $('.video_zoom_speed_label').text(zoomSpeed.toFixed(1) + 'x');
  });
  // Joystick setup
  setupJoystick();
  
  // Update preview when parameters change
  $('.video_speed, .video_zoom, .video_zoom_speed, .end_line_amount, .end_line_width, .end_line_width_variation, .end_padding, .end_border_width').on('input change', function() {
    // Preview will automatically use new values on next frame
  });
});

function setupJoystick() {
  var container = document.getElementById('joystick-container');
  var handle = document.getElementById('joystick-handle');
  var containerRect = container.getBoundingClientRect();
  var containerSize = 200;
  var handleSize = 40;
  var maxDistance = (containerSize - handleSize) / 2;
  
  function updateJoystick(clientX, clientY) {
    var rect = container.getBoundingClientRect();
    var centerX = rect.left + rect.width / 2;
    var centerY = rect.top + rect.height / 2;
    
    var deltaX = clientX - centerX;
    var deltaY = clientY - centerY;
    var distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
    
    // Limit to circle
    if (distance > maxDistance) {
      deltaX = (deltaX / distance) * maxDistance;
      deltaY = (deltaY / distance) * maxDistance;
      distance = maxDistance;
    }
    
    // Update handle position
    handle.style.transform = 'translate(calc(-50% + ' + deltaX + 'px), calc(-50% + ' + deltaY + 'px))';
    
    // Calculate normalized values (-1.0 to 1.0)
    gyroX = deltaX / maxDistance;
    gyroY = -deltaY / maxDistance; // Invert Y for intuitive up/down
    
    // Update labels
    $('.gyro_x_label').text(gyroX.toFixed(2));
    $('.gyro_y_label').text(gyroY.toFixed(2));
  }
  
  function handleMove(e) {
    if (!isJoystickDragging) return;
    e.preventDefault();
    var clientX = e.touches ? e.touches[0].clientX : e.clientX;
    var clientY = e.touches ? e.touches[0].clientY : e.clientY;
    updateJoystick(clientX, clientY);
  }
  
  function handleEnd() {
    isJoystickDragging = false;
  }
  
  function handleStart(e) {
    isJoystickDragging = true;
    var clientX = e.touches ? e.touches[0].clientX : e.clientX;
    var clientY = e.touches ? e.touches[0].clientY : e.clientY;
    updateJoystick(clientX, clientY);
  }
  
  // Mouse events
  container.addEventListener('mousedown', handleStart);
  document.addEventListener('mousemove', handleMove);
  document.addEventListener('mouseup', handleEnd);
  
  // Touch events
  container.addEventListener('touchstart', handleStart);
  document.addEventListener('touchmove', handleMove);
  document.addEventListener('touchend', handleEnd);
}

function resetJoystick() {
  gyroX = 0.0;
  gyroY = 0.0;
  var handle = document.getElementById('joystick-handle');
  handle.style.transform = 'translate(-50%, -50%)';
  $('.gyro_x_label').text('0.00');
  $('.gyro_y_label').text('0.00');
}
