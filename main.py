import eel
import art_gen

# Store art states for video generation
art_states = {}

@eel.expose
def generate_art(size, amount, line_width, line_width_variation, padding, border_width):
    result = art_gen.gen_art(size, amount, line_width, line_width_variation, padding, border_width)
    if isinstance(result, tuple):
        img_data, state = result
        # Store state with a unique ID
        import time
        state_id = str(int(time.time() * 1000000))
        art_states[state_id] = {
            'state': state,
            'params': {
                'size': int(size),
                'amount': int(amount),
                'line_width': int(line_width),
                'line_width_variation': float(line_width_variation),
                'padding': int(padding),
                'border_width': int(border_width)
            }
        }
        return {'image': img_data, 'state_id': state_id}
    return {'image': result, 'state_id': None}

@eel.expose
def generate_realtime_frame(state_id, time_factor, video_speed, video_zoom, video_zoom_speed, gyro_x, gyro_y, end_amount, end_line_width, end_line_width_variation, end_padding, end_border_width):
    """Generate a single frame for real-time preview."""
    if state_id not in art_states:
        return {'error': 'Art state not found'}
    
    stored = art_states[state_id]
    art_state = stored['state']
    start_params = stored['params']
    
    end_params = {
        'size': start_params['size'],
        'amount': int(end_amount),
        'line_width': int(end_line_width),
        'line_width_variation': float(end_line_width_variation),
        'padding': start_params['padding'],
        'border_width': int(end_border_width)
    }
    
    try:
        frame_data = art_gen.generate_frame_at_time(
            art_state, start_params, end_params,
            float(time_factor),
            speed=float(video_speed),
            zoom=float(video_zoom),
            zoom_speed=float(video_zoom_speed),
            gyro_x=float(gyro_x),
            gyro_y=float(gyro_y)
        )
        return {'frame': frame_data}
    except Exception as e:
        return {'error': str(e)}

@eel.expose
def generate_video(state_id, video_speed, video_zoom, video_zoom_speed, end_amount, end_line_width, end_line_width_variation, end_padding, end_border_width):
    if state_id not in art_states:
        return {'error': 'Art state not found'}
    
    stored = art_states[state_id]
    art_state = stored['state']
    start_params = stored['params']
    
    end_params = {
        'size': start_params['size'],  # Keep size constant
        'amount': int(end_amount),
        'line_width': int(end_line_width),
        'line_width_variation': float(end_line_width_variation),
        'padding': start_params['padding'],  # Keep padding constant
        'border_width': int(end_border_width)
    }
    
    try:
        video_data = art_gen.generate_video(art_state, start_params, end_params, duration_seconds=30, fps=10, speed=float(video_speed), zoom=float(video_zoom), zoom_speed=float(video_zoom_speed))
        return {'video': video_data}
    except Exception as e:
        return {'error': str(e)}

eel.init('www')
eel.start('index.html', port = 2000)
