from PIL import Image, ImageDraw
import random
from math import sqrt
import base64
from io import BytesIO
import os
import tempfile
try:
    import imageio  # type: ignore
    IMAGEIO_AVAILABLE = True
except ImportError:
    IMAGEIO_AVAILABLE = False

def compare_clrs(clr1, clr2):
    r, g, b = clr1
    r2, g2, b2 = clr2
    distance = pow((r - r2), 2) + pow((g - g2), 2) + pow((b - b2), 2)
    distance = sqrt(distance)
    return distance

def rand_clr(colors):
    if colors != []:
        restart = True
        while restart:
            new_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            for index, color in enumerate(colors):
                if compare_clrs(new_color, color) < 200:
                    break
                elif index == len(colors) - 1:
                    restart = False
                    break
        return new_color
    else:
        return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

def interpolate(start_clr, end_clr, factor: float):
    recip = 1 - factor
    return (
        int(start_clr[0] * recip + end_clr[0] * factor),
        int(start_clr[1] * recip + end_clr[1] * factor),
        int(start_clr[2] * recip + end_clr[2] * factor)
    )

def gen_art(size, amount, line_width, line_width_variation, padding, border_width, seed=None, art_state=None):
    """
    Generate art with optional seed for deterministic generation.
    If art_state is provided, it will use those exact values instead of generating new random ones.
    """
    size = int(size)
    amount = int(amount)
    line_width = int(line_width)
    padding = int(padding)
    border_width = int(border_width)
    
    # Set seed if provided for deterministic generation
    if seed is not None:
        random.seed(seed)
    
    colors = []
    image_size = size
    if padding > 0:
        image_padding = padding
    else:
        image_padding = 1
    
    # Use provided art_state if available, otherwise generate new random values
    if art_state:
        start_clr = tuple(art_state['start_clr'])
        end_clr = tuple(art_state['end_clr'])
        image_bg_clr = tuple(art_state['image_bg_clr'])
        border_clr = tuple(art_state['border_clr'])
        initial_point = tuple(art_state['initial_point'])
        line_end_points = [tuple(p) for p in art_state['line_end_points']]
        line_width_variations = art_state['line_width_variations']
        # Get curve control points from state, or generate if not present (for backward compatibility)
        if 'curve_control_points' in art_state:
            # Handle both old format (single control point) and new format (two control points)
            if art_state['curve_control_points'] and isinstance(art_state['curve_control_points'][0], list) and len(art_state['curve_control_points'][0]) == 2:
                # New format: list of [control1, control2]
                curve_control_points = [[tuple(p[0]), tuple(p[1])] for p in art_state['curve_control_points']]
            else:
                # Old format: single control point, convert to new format
                old_controls = [tuple(p) if isinstance(p, (list, tuple)) else p for p in art_state['curve_control_points']]
                curve_control_points = []
                for ctrl in old_controls:
                    # Create second control point near the first for smooth transition
                    ctrl2 = (ctrl[0] + random.randint(-50, 50), ctrl[1] + random.randint(-50, 50))
                    ctrl2 = (max(image_padding, min(image_size - image_padding, ctrl2[0])),
                            max(image_padding, min(image_size - image_padding, ctrl2[1])))
                    curve_control_points.append([ctrl, ctrl2])
        else:
            # Generate control points if not in state (for old art states)
            curve_control_points = []
            for i in range(amount):
                ctrl1 = (random.randint(image_padding, image_size - image_padding), 
                        random.randint(image_padding, image_size - image_padding))
                ctrl2 = (random.randint(image_padding, image_size - image_padding), 
                        random.randint(image_padding, image_size - image_padding))
                curve_control_points.append([ctrl1, ctrl2])
        
        # Get line start points for branching, or generate if not present
        if 'line_start_points' in art_state:
            line_start_points = art_state['line_start_points']
        else:
            # Generate branching pattern for backward compatibility
            line_start_points = []
            for i in range(amount):
                if i == 0:
                    line_start_points.append(None)
                elif i < amount * 0.3:
                    line_start_points.append(random.randint(0, i - 1))
                else:
                    line_start_points.append(None)
    else:
        start_clr = rand_clr(colors)
        colors.append(start_clr)
        end_clr = rand_clr(colors)
        colors.append(end_clr)
        image_bg_clr = rand_clr(colors)
        colors.append(image_bg_clr)
        border_clr = rand_clr(colors)
        colors.append(border_clr)
        initial_point = (random.randint(image_padding, image_size - image_padding), 
                        random.randint(image_padding, image_size - image_padding))
        # Pre-generate all line points, variations, and curve control points
        # Create more complex geometry by generating multiple control points per line
        line_end_points = []
        line_width_variations = []
        curve_control_points = []
        # Generate starting points for lines (for more complex branching)
        line_start_points = []
        
        for i in range(amount):
            line_end_points.append((random.randint(image_padding, image_size - image_padding), 
                                   random.randint(image_padding, image_size - image_padding)))
            line_width_variations.append(random.randint(0, int(line_width_variation)))
            
            # Generate multiple control points for more complex curves (2 control points = cubic bezier)
            # Make them more psychedelic with extreme positions and variations
            import math
            # Create more extreme control points for psychedelic curves
            # Use polar coordinates with dramatic variations
            center_x = image_size / 2
            center_y = image_size / 2
            
            # Control point 1: Spiral/wave pattern
            angle1 = random.uniform(0, math.pi * 2)
            radius1 = random.uniform(image_size * 0.2, image_size * 0.45)  # More extreme range
            ctrl1_x = center_x + math.cos(angle1) * radius1 + random.uniform(-image_size * 0.1, image_size * 0.1)
            ctrl1_y = center_y + math.sin(angle1) * radius1 + random.uniform(-image_size * 0.1, image_size * 0.1)
            control1 = (
                max(image_padding, min(image_size - image_padding, int(ctrl1_x))),
                max(image_padding, min(image_size - image_padding, int(ctrl1_y)))
            )
            
            # Control point 2: Opposite side with wave variation
            angle2 = angle1 + math.pi + random.uniform(-0.5, 0.5)  # Opposite side with variation
            radius2 = random.uniform(image_size * 0.2, image_size * 0.45)
            # Add wave distortion
            wave_offset = math.sin(angle2 * 3) * image_size * 0.15
            ctrl2_x = center_x + math.cos(angle2) * radius2 + wave_offset + random.uniform(-image_size * 0.1, image_size * 0.1)
            ctrl2_y = center_y + math.sin(angle2) * radius2 + wave_offset + random.uniform(-image_size * 0.1, image_size * 0.1)
            control2 = (
                max(image_padding, min(image_size - image_padding, int(ctrl2_x))),
                max(image_padding, min(image_size - image_padding, int(ctrl2_y)))
            )
            
            curve_control_points.append([control1, control2])  # Two control points for cubic bezier
            
            # Generate starting points - create branching patterns instead of always from center
            if i == 0:
                # First line starts from initial point
                line_start_points.append(None)  # None means use last_point
            elif i < amount * 0.3:  # 30% branch from previous lines
                # Branch from a random previous point
                branch_from = random.randint(0, i - 1)
                line_start_points.append(branch_from)
            else:
                # Most lines continue from last point (creates flowing chains)
                line_start_points.append(None)  # None means use last_point
    
    image = Image.new('RGB', (image_size, image_size), image_bg_clr)
   
    #Draw interface
    draw = ImageDraw.Draw(image)

    #Draw border
    draw.rectangle((0, 0, image_size - 1, image_size - 1), outline=border_clr, width=border_width)

    #Draw lines with complex curves
    line_amount = amount
    last_point = initial_point
    previous_end_points = [initial_point]  # Track all previous end points for branching
    
    def draw_cubic_bezier_curve(draw, start, control1, control2, end, color, width, segments=30):
        """Draw a cubic bezier curve using multiple line segments for more complex curves."""
        points = []
        for i in range(segments + 1):
            t = i / segments
            # Cubic bezier formula: (1-t)³P₀ + 3(1-t)²tP₁ + 3(1-t)t²P₂ + t³P₃
            x = int((1-t)**3 * start[0] + 3*(1-t)**2*t * control1[0] + 3*(1-t)*t**2 * control2[0] + t**3 * end[0])
            y = int((1-t)**3 * start[1] + 3*(1-t)**2*t * control1[1] + 3*(1-t)*t**2 * control2[1] + t**3 * end[1])
            points.append((x, y))
        
        # Draw curve as connected line segments
        for j in range(len(points) - 1):
            draw.line([points[j], points[j+1]], color, width)
    
    for i in range(line_amount):
        # Use pre-generated values (either from art_state or generated above)
        rand_y = tuple(line_end_points[i])
        line_width_with_varation = line_width + line_width_variations[i]
        controls = curve_control_points[i]
        control1 = tuple(controls[0])
        control2 = tuple(controls[1])
        
        # Determine starting point for this line - create complex branching patterns
        if line_start_points[i] is None:
            # Continue from last point (creates flowing chains)
            rand_x = last_point
        elif isinstance(line_start_points[i], int):
            # Branch from a previous line's end point
            branch_index = line_start_points[i]
            if branch_index < len(previous_end_points):
                rand_x = previous_end_points[branch_index]
            else:
                rand_x = last_point
        else:
            rand_x = last_point
        
        line_color = interpolate(start_clr, end_clr, i / (line_amount - 1) if line_amount > 1 else 0)
       
        # Draw complex curved line using cubic bezier curve (more organic and flowing)
        draw_cubic_bezier_curve(draw, rand_x, control1, control2, rand_y, line_color, line_width_with_varation)
        last_point = rand_y
        previous_end_points.append(rand_y)  # Track for branching
   
    #return Image
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    # Return image and state for video generation
    if art_state is None:
        # Create state object for this generation
        state = {
            'start_clr': list(start_clr),
            'end_clr': list(end_clr),
            'image_bg_clr': list(image_bg_clr),
            'border_clr': list(border_clr),
            'initial_point': list(initial_point),
            'line_end_points': [list(p) for p in line_end_points],
            'line_width_variations': line_width_variations,
            'curve_control_points': [[list(p[0]), list(p[1])] for p in curve_control_points],
            'line_start_points': line_start_points
        }
        return 'data:image/png;base64, ' + img_str, state
    else:
        return 'data:image/png;base64, ' + img_str

def interpolate_params(start_params, end_params, factor):
    """Interpolate between two parameter sets."""
    result = {}
    for key in start_params:
        if isinstance(start_params[key], (int, float)):
            result[key] = start_params[key] + (end_params[key] - start_params[key]) * factor
        elif isinstance(start_params[key], list) and len(start_params[key]) == 3:
            # Color interpolation
            result[key] = [
                int(start_params[key][0] + (end_params[key][0] - start_params[key][0]) * factor),
                int(start_params[key][1] + (end_params[key][1] - start_params[key][1]) * factor),
                int(start_params[key][2] + (end_params[key][2] - start_params[key][2]) * factor)
            ]
        else:
            result[key] = start_params[key]
    return result

def scale_points(points, old_size, new_size, old_padding, new_padding):
    """Scale points from old size to new size proportionally."""
    if old_size == new_size and old_padding == new_padding:
        return points
    
    old_usable = old_size - 2 * old_padding if old_padding > 0 else old_size - 2
    new_usable = new_size - 2 * new_padding if new_padding > 0 else new_size - 2
    
    scaled_points = []
    for point in points:
        # Normalize to 0-1 range within usable area
        x_norm = (point[0] - old_padding) / old_usable if old_usable > 0 else 0.5
        y_norm = (point[1] - old_padding) / old_usable if old_usable > 0 else 0.5
        
        # Scale to new size
        new_x = int(x_norm * new_usable + new_padding) if new_padding > 0 else int(x_norm * new_usable + 1)
        new_y = int(y_norm * new_usable + new_padding) if new_padding > 0 else int(y_norm * new_usable + 1)
        
        # Clamp to valid range
        new_x = max(new_padding if new_padding > 0 else 1, min(new_size - new_padding - 1 if new_padding > 0 else new_size - 1, new_x))
        new_y = max(new_padding if new_padding > 0 else 1, min(new_size - new_padding - 1 if new_padding > 0 else new_size - 1, new_y))
        
        scaled_points.append([new_x, new_y])
    
    return scaled_points

def generate_end_colors(start_colors):
    """Generate end colors by shifting the start colors in HSV space for smooth transitions."""
    from colorsys import rgb_to_hsv, hsv_to_rgb
    
    end_colors = {}
    for key, color in start_colors.items():
        r, g, b = color[0] / 255.0, color[1] / 255.0, color[2] / 255.0
        h, s, v = rgb_to_hsv(r, g, b)
        
        # Shift hue by 60-120 degrees for interesting color transitions
        import random
        random.seed(hash(key) % 1000)  # Deterministic but different for each color
        hue_shift = random.uniform(0.15, 0.35)  # 60-120 degrees
        new_h = (h + hue_shift) % 1.0
        
        # Slightly adjust saturation and value
        new_s = max(0.3, min(1.0, s + random.uniform(-0.2, 0.2)))
        new_v = max(0.4, min(1.0, v + random.uniform(-0.2, 0.2)))
        
        new_r, new_g, new_b = hsv_to_rgb(new_h, new_s, new_v)
        end_colors[key] = [int(new_r * 255), int(new_g * 255), int(new_b * 255)]
    
    return end_colors

def generate_end_points(start_points, image_size, padding):
    """Generate end positions for line points with psychedelic, chaotic movement patterns."""
    import random
    import math
    
    end_points = []
    image_padding = padding if padding > 0 else 1
    center_x = image_size / 2.0
    center_y = image_size / 2.0
    
    for i, point in enumerate(start_points):
        # Use point index as seed for deterministic but varied movement
        random.seed(hash((point[0], point[1], i)) % 10000)
        
        # Create more psychedelic, chaotic movement patterns
        # Combine multiple movement types for more complex geometry
        
        # 1. Spiral movement (rotates around center with changing radius)
        dx = point[0] - center_x
        dy = point[1] - center_y
        angle = math.atan2(dy, dx)
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Smooth angle rotation (less extreme)
        angle_shift = random.uniform(1.0, 3.0)  # 180-540 degrees rotation (reduced from 2-6)
        new_angle = angle + angle_shift
        
        # Moderate distance variation (smoother spiral)
        distance_factor = random.uniform(0.6, 1.5)  # Reduced variation for smoother effect
        new_distance = distance * distance_factor
        
        # 2. Add smooth wave/sine patterns for psychedelic effect
        wave_amplitude = image_size * random.uniform(0.05, 0.15)  # Reduced amplitude
        wave_frequency = random.uniform(1.5, 3.0)  # Lower frequency for smoother waves
        wave_phase = random.uniform(0, math.pi * 2)
        wave_x = math.sin(new_angle * wave_frequency + wave_phase) * wave_amplitude
        wave_y = math.cos(new_angle * wave_frequency + wave_phase) * wave_amplitude
        
        # 3. Add moderate random offset (less chaotic)
        chaos_range = image_size * random.uniform(0.1, 0.3)  # Reduced chaos
        chaos_x = random.uniform(-chaos_range, chaos_range)
        chaos_y = random.uniform(-chaos_range, chaos_range)
        
        # Combine all movements for maximum psychedelic effect
        spiral_x = center_x + math.cos(new_angle) * new_distance
        spiral_y = center_y + math.sin(new_angle) * new_distance
        
        new_x = spiral_x + wave_x + chaos_x
        new_y = spiral_y + wave_y + chaos_y
        
        # Clamp to valid range
        new_x = max(image_padding, min(image_size - image_padding - 1, int(new_x)))
        new_y = max(image_padding, min(image_size - image_padding - 1, int(new_y)))
        
        end_points.append([new_x, new_y])
    
    return end_points

def generate_frame_at_time(art_state, start_params, end_params, time_factor, speed=1.0, zoom=1.1, zoom_speed=0.0, gyro_x=0.0, gyro_y=0.0):
    """
    Generate a single frame at a specific time factor (0.0 to 1.0) for real-time preview.
    
    Args:
        art_state: The deterministic art state (colors, points, etc.)
        start_params: Starting parameters
        end_params: Ending parameters
        time_factor: Time position (0.0 to 1.0)
        speed: Animation speed multiplier
        zoom: Starting zoom level
        zoom_speed: How fast zoom changes
    """
    import math
    
    original_size = start_params['size']
    original_padding = start_params['padding']
    original_amount = len(art_state['line_end_points'])
    
    # Normalize speed: 20.0 becomes 1.0x, so divide by 20
    normalized_speed = speed / 20.0
    
    # Generate multiple color sets for smooth continuous transitions
    start_colors = {
        'start_clr': art_state['start_clr'],
        'end_clr': art_state['end_clr'],
        'image_bg_clr': art_state['image_bg_clr'],
        'border_clr': art_state['border_clr']
    }
    color_set_1 = generate_end_colors(start_colors)
    color_set_2 = generate_end_colors(color_set_1)
    color_set_3 = generate_end_colors(color_set_2)
    color_sets = [start_colors, color_set_1, color_set_2, color_set_3]
    
    # Generate end positions for line points
    start_line_points = art_state['line_end_points']
    end_line_points = generate_end_points(start_line_points, original_size, original_padding)
    start_initial_point = art_state['initial_point']
    end_initial_point = generate_end_points([start_initial_point], original_size, original_padding)[0]
    
    # Generate end positions for curve control points
    if 'curve_control_points' in art_state and len(art_state['curve_control_points']) > 0:
        start_control_points = art_state['curve_control_points']
        end_control_points = []
        for ctrl_pair in start_control_points:
            if isinstance(ctrl_pair, list) and len(ctrl_pair) == 2 and isinstance(ctrl_pair[0], list):
                end_ctrl1 = generate_end_points([ctrl_pair[0]], original_size, original_padding)[0]
                end_ctrl2 = generate_end_points([ctrl_pair[1]], original_size, original_padding)[0]
                end_control_points.append([end_ctrl1, end_ctrl2])
            else:
                old_ctrl = ctrl_pair if isinstance(ctrl_pair, (list, tuple)) else list(ctrl_pair)
                end_ctrl1 = generate_end_points([old_ctrl], original_size, original_padding)[0]
                end_ctrl2 = generate_end_points([old_ctrl], original_size, original_padding)[0]
                end_control_points.append([end_ctrl1, end_ctrl2])
    else:
        start_control_points = []
        end_control_points = []
    
    # Calculate factors
    base_factor = time_factor
    
    # Colors progress forward continuously
    color_progress = base_factor * normalized_speed * len(color_sets)
    color_set_index = int(color_progress) % len(color_sets)
    next_color_set_index = (color_set_index + 1) % len(color_sets)
    color_factor = color_progress % 1.0
    current_color_set = color_sets[color_set_index]
    next_color_set = color_sets[next_color_set_index]
    
    # Geometry movement - 12x faster than colors
    geometry_time = base_factor * normalized_speed * 12.0
    geometry_factor = geometry_time
    
    # Calculate gyro values early (needed for color and geometry effects)
    gyro_distance = math.sqrt(gyro_x * gyro_x + gyro_y * gyro_y)
    gyro_angle = math.atan2(gyro_y, gyro_x)  # Angle of gyro position
    
    # Interpolate parameters
    current_params = interpolate_params(start_params, end_params, geometry_factor)
    current_params['size'] = original_size
    current_params['padding'] = original_padding
    current_amount = int(current_params['amount'])
    
    # Create modified state
    modified_state = art_state.copy()
    
    # Interpolate colors with gyro-based hue shift
    from colorsys import rgb_to_hsv, hsv_to_rgb
    
    # Apply gyro-based color shift (hue rotation based on gyro position)
    # Gyro creates a noticeable color shift - stronger when further from center
    hue_shift = gyro_angle / (2.0 * math.pi)  # Convert angle to 0-1 range
    hue_shift_amount = gyro_distance * 0.3  # Up to 30% hue shift at max distance
    
    def apply_gyro_color_shift(rgb_color, hue_shift, shift_amount):
        """Apply hue shift to a color based on gyro."""
        r, g, b = rgb_color[0] / 255.0, rgb_color[1] / 255.0, rgb_color[2] / 255.0
        h, s, v = rgb_to_hsv(r, g, b)
        # Shift hue based on gyro angle and distance
        new_h = (h + hue_shift * shift_amount) % 1.0
        # Also slightly adjust saturation based on gyro distance
        new_s = max(0.3, min(1.0, s + (gyro_distance * 0.2 - 0.1)))
        new_r, new_g, new_b = hsv_to_rgb(new_h, new_s, v)
        return [int(new_r * 255), int(new_g * 255), int(new_b * 255)]
    
    # Get base interpolated colors
    base_start_clr = [
        int(current_color_set['start_clr'][0] + (next_color_set['start_clr'][0] - current_color_set['start_clr'][0]) * color_factor),
        int(current_color_set['start_clr'][1] + (next_color_set['start_clr'][1] - current_color_set['start_clr'][1]) * color_factor),
        int(current_color_set['start_clr'][2] + (next_color_set['start_clr'][2] - current_color_set['start_clr'][2]) * color_factor)
    ]
    base_end_clr = [
        int(current_color_set['end_clr'][0] + (next_color_set['end_clr'][0] - current_color_set['end_clr'][0]) * color_factor),
        int(current_color_set['end_clr'][1] + (next_color_set['end_clr'][1] - current_color_set['end_clr'][1]) * color_factor),
        int(current_color_set['end_clr'][2] + (next_color_set['end_clr'][2] - current_color_set['end_clr'][2]) * color_factor)
    ]
    base_bg_clr = [
        int(current_color_set['image_bg_clr'][0] + (next_color_set['image_bg_clr'][0] - current_color_set['image_bg_clr'][0]) * color_factor),
        int(current_color_set['image_bg_clr'][1] + (next_color_set['image_bg_clr'][1] - current_color_set['image_bg_clr'][1]) * color_factor),
        int(current_color_set['image_bg_clr'][2] + (next_color_set['image_bg_clr'][2] - current_color_set['image_bg_clr'][2]) * color_factor)
    ]
    base_border_clr = [
        int(current_color_set['border_clr'][0] + (next_color_set['border_clr'][0] - current_color_set['border_clr'][0]) * color_factor),
        int(current_color_set['border_clr'][1] + (next_color_set['border_clr'][1] - current_color_set['border_clr'][1]) * color_factor),
        int(current_color_set['border_clr'][2] + (next_color_set['border_clr'][2] - current_color_set['border_clr'][2]) * color_factor)
    ]
    
    # Apply gyro color shift
    modified_state['start_clr'] = apply_gyro_color_shift(base_start_clr, hue_shift, hue_shift_amount)
    modified_state['end_clr'] = apply_gyro_color_shift(base_end_clr, hue_shift, hue_shift_amount)
    modified_state['image_bg_clr'] = apply_gyro_color_shift(base_bg_clr, hue_shift, hue_shift_amount * 0.5)  # Less shift for background
    modified_state['border_clr'] = apply_gyro_color_shift(base_border_clr, hue_shift, hue_shift_amount)
    
    # Handle amount
    if current_amount > original_amount:
        current_amount = original_amount
    
    # Calculate dynamic zoom
    if zoom_speed > 0:
        zoom_oscillation = math.sin(base_factor * math.pi * 2 * zoom_speed) * 0.3
        current_zoom = zoom + zoom_oscillation
        current_zoom = max(0.5, min(2.0, current_zoom))
    else:
        current_zoom = zoom
    
    # Calculate bounds
    image_center = original_size / 2.0
    image_padding = original_padding if original_padding > 0 else 1
    
    # Apply gyro offset to center (creates very noticeable shift effect)
    # Gyro values range from -1.0 to 1.0, map to significant offset
    # Increased to 0.8 for maximum noticeable effect
    gyro_offset_x = gyro_x * original_size * 0.8  # Up to 80% of image size
    gyro_offset_y = gyro_y * original_size * 0.8
    effective_center_x = image_center + gyro_offset_x
    effective_center_y = image_center + gyro_offset_y
    
    if current_zoom < 1.0:
        zoomed_size = original_size * current_zoom
        zoom_offset = (original_size - zoomed_size) / 2.0
        min_bound = max(image_padding, int(zoom_offset))
        max_bound = min(original_size - image_padding - 1, int(original_size - zoom_offset - 1))
    else:
        min_bound = image_padding
        max_bound = original_size - image_padding - 1
    
    # Animate line points
    animated_line_points = []
    points_to_use = min(current_amount, len(start_line_points))
    for i in range(points_to_use):
        start_pt = start_line_points[i]
        end_pt = end_line_points[i]
        animated_x = start_pt[0] + (end_pt[0] - start_pt[0]) * geometry_factor
        animated_y = start_pt[1] + (end_pt[1] - start_pt[1]) * geometry_factor
        
        # Add smooth psychedelic wave distortions
        wave_phase = i * 0.3 + geometry_factor * 1.5
        wave_amplitude = original_size * 0.04
        wave_x = math.sin(wave_phase) * wave_amplitude
        wave_y = math.cos(wave_phase * 1.2) * wave_amplitude
        
        # Add gentle spiral rotation with gyro-based additional rotation
        rel_to_center_x = animated_x - image_center
        rel_to_center_y = animated_y - image_center
        
        # Base rotation from animation
        base_rotation_angle = geometry_factor * math.pi * 0.2
        
        # Add gyro-based rotation (tilt effect based on gyro position)
        # Gyro creates noticeable rotation - stronger when further from center
        gyro_rotation = gyro_distance * math.pi * 0.3  # Up to ~54 degrees rotation at max distance
        # Rotation direction follows gyro angle
        total_rotation = base_rotation_angle + gyro_rotation * math.cos(gyro_angle)
        
        rotated_x = rel_to_center_x * math.cos(total_rotation) - rel_to_center_y * math.sin(total_rotation)
        rotated_y = rel_to_center_x * math.sin(total_rotation) + rel_to_center_y * math.cos(total_rotation)
        
        # Add gyro-based distortion (stretch/compress based on gyro direction)
        # Creates a noticeable perspective/distortion effect
        distortion_factor = 1.0 + gyro_distance * 0.4  # Up to 40% stretch/compress
        # Distort along gyro angle direction
        distortion_x = rotated_x * (1.0 + (distortion_factor - 1.0) * math.cos(gyro_angle) * 0.5)
        distortion_y = rotated_y * (1.0 + (distortion_factor - 1.0) * math.sin(gyro_angle) * 0.5)
        
        # Apply gyro offset to rotation center (creates noticeable tilt/shift effect)
        psychedelic_x = effective_center_x + distortion_x + wave_x
        psychedelic_y = effective_center_y + distortion_y + wave_y
        
        # Apply zoom relative to effective center
        rel_x = psychedelic_x - effective_center_x
        rel_y = psychedelic_y - effective_center_y
        zoomed_x = effective_center_x + rel_x * current_zoom
        zoomed_y = effective_center_y + rel_y * current_zoom
        
        animated_x = max(min_bound, min(max_bound, int(round(zoomed_x))))
        animated_y = max(min_bound, min(max_bound, int(round(zoomed_y))))
        
        animated_line_points.append([animated_x, animated_y])
    
    modified_state['line_end_points'] = animated_line_points
    
    # Animate control points
    if len(start_control_points) > 0:
        animated_control_points = []
        for i in range(points_to_use):
            if i < len(start_control_points):
                start_ctrls = start_control_points[i]
                end_ctrls = end_control_points[i]
                
                if isinstance(start_ctrls, list) and len(start_ctrls) == 2 and isinstance(start_ctrls[0], list):
                    start_ctrl1 = start_ctrls[0]
                    start_ctrl2 = start_ctrls[1]
                    end_ctrl1 = end_ctrls[0]
                    end_ctrl2 = end_ctrls[1]
                else:
                    import random
                    start_ctrl1 = start_ctrls if isinstance(start_ctrls, (list, tuple)) else list(start_ctrls)
                    end_ctrl1 = end_ctrls if isinstance(end_ctrls, (list, tuple)) else list(end_ctrls)
                    start_ctrl2 = [start_ctrl1[0] + random.randint(-30, 30), start_ctrl1[1] + random.randint(-30, 30)]
                    end_ctrl2 = [end_ctrl1[0] + random.randint(-30, 30), end_ctrl1[1] + random.randint(-30, 30)]
                
                ctrl1_x = start_ctrl1[0] + (end_ctrl1[0] - start_ctrl1[0]) * geometry_factor
                ctrl1_y = start_ctrl1[1] + (end_ctrl1[1] - start_ctrl1[1]) * geometry_factor
                ctrl2_x = start_ctrl2[0] + (end_ctrl2[0] - start_ctrl2[0]) * geometry_factor
                ctrl2_y = start_ctrl2[1] + (end_ctrl2[1] - start_ctrl2[1]) * geometry_factor
                
                # Apply gyro offset to control points
                rel_x1 = ctrl1_x - effective_center_x
                rel_y1 = ctrl1_y - effective_center_y
                zoomed_x1 = effective_center_x + rel_x1 * current_zoom
                zoomed_y1 = effective_center_y + rel_y1 * current_zoom
                
                rel_x2 = ctrl2_x - effective_center_x
                rel_y2 = ctrl2_y - effective_center_y
                zoomed_x2 = effective_center_x + rel_x2 * current_zoom
                zoomed_y2 = effective_center_y + rel_y2 * current_zoom
                
                animated_control_points.append([
                    [max(min_bound, min(max_bound, int(round(zoomed_x1)))),
                     max(min_bound, min(max_bound, int(round(zoomed_y1))))],
                    [max(min_bound, min(max_bound, int(round(zoomed_x2)))),
                     max(min_bound, min(max_bound, int(round(zoomed_y2))))]
                ])
        modified_state['curve_control_points'] = animated_control_points
    
    # Animate initial point
    animated_x = start_initial_point[0] + (end_initial_point[0] - start_initial_point[0]) * geometry_factor
    animated_y = start_initial_point[1] + (end_initial_point[1] - start_initial_point[1]) * geometry_factor
    
    # Apply gyro offset to initial point
    rel_x = animated_x - effective_center_x
    rel_y = animated_y - effective_center_y
    zoomed_x = effective_center_x + rel_x * current_zoom
    zoomed_y = effective_center_y + rel_y * current_zoom
    
    animated_initial = [
        max(min_bound, min(max_bound, int(round(zoomed_x)))),
        max(min_bound, min(max_bound, int(round(zoomed_y))))
    ]
    modified_state['initial_point'] = animated_initial
    
    # Handle line_width_variations and line_start_points
    if current_amount < original_amount:
        modified_state['line_width_variations'] = art_state['line_width_variations'][:current_amount]
        if 'line_start_points' in art_state:
            modified_state['line_start_points'] = art_state['line_start_points'][:current_amount]
    else:
        modified_state['line_width_variations'] = art_state['line_width_variations']
        if 'line_start_points' in art_state:
            modified_state['line_start_points'] = art_state['line_start_points']
        elif 'line_start_points' not in modified_state:
            import random
            line_start_points = []
            for j in range(current_amount):
                if j == 0:
                    line_start_points.append(None)
                elif j < current_amount * 0.3:
                    line_start_points.append(random.randint(0, j - 1))
                else:
                    line_start_points.append(None)
            modified_state['line_start_points'] = line_start_points
    
    # Generate frame
    frame_result = gen_art(
        original_size,
        current_amount,
        current_params['line_width'],
        current_params['line_width_variation'],
        original_padding,
        current_params['border_width'],
        art_state=modified_state
    )
    
    # Return frame data directly (gen_art already returns base64 encoded image)
    return frame_result

def generate_video(art_state, start_params, end_params, duration_seconds=30, fps=10, speed=1.0, zoom=1.1, zoom_speed=0.0):
    """
    Generate a video by slowly tweaking parameters over time.
    Interpolates ALL parameters including colors for smooth animation.
    
    Args:
        art_state: The deterministic art state (colors, points, etc.)
        start_params: Starting parameters (size, amount, line_width, etc.)
        end_params: Ending parameters to interpolate to
        duration_seconds: Video duration in seconds
        fps: Frames per second (lower = faster generation)
        speed: Animation speed multiplier (1.0 = normal, 2.0 = 2x faster, 0.5 = 2x slower)
        zoom: Starting zoom level (0.5-2.0) - <1.0 creates more room for movement, >1.0 zooms in (no edges)
        zoom_speed: How fast zoom changes (0.0 = static, higher = zooms in/out over time)
    """
    if not IMAGEIO_AVAILABLE:
        raise ImportError("imageio is required for video generation. Install it with: pip install imageio imageio-ffmpeg")
    
    total_frames = duration_seconds * fps
    frames = []
    
    # Create temporary directory for frames
    temp_dir = tempfile.mkdtemp()
    
    # Store original state - size stays constant throughout video
    original_size = start_params['size']
    original_padding = start_params['padding']
    original_amount = len(art_state['line_end_points'])
    
    # Determine target video size (use original size, rounded to multiple of 16)
    target_video_size = ((original_size + 8) // 16) * 16  # Round up to nearest multiple of 16
    
    # Generate multiple color sets for smooth continuous transitions
    # This prevents abrupt color changes when cycling
    start_colors = {
        'start_clr': art_state['start_clr'],
        'end_clr': art_state['end_clr'],
        'image_bg_clr': art_state['image_bg_clr'],
        'border_clr': art_state['border_clr']
    }
    # Generate a sequence of color sets to cycle through smoothly
    color_set_1 = generate_end_colors(start_colors)
    color_set_2 = generate_end_colors(color_set_1)
    color_set_3 = generate_end_colors(color_set_2)
    # Store all color sets for smooth cycling
    color_sets = [start_colors, color_set_1, color_set_2, color_set_3]
    
    # Generate end positions for line points to animate geometry
    start_line_points = art_state['line_end_points']
    end_line_points = generate_end_points(start_line_points, original_size, original_padding)
    
    # Generate end position for initial point
    start_initial_point = art_state['initial_point']
    end_initial_point = generate_end_points([start_initial_point], original_size, original_padding)[0]
    
    # Generate end positions for curve control points if they exist
    # Now each line has 2 control points for cubic bezier curves
    if 'curve_control_points' in art_state and len(art_state['curve_control_points']) > 0:
        start_control_points = art_state['curve_control_points']
        # Generate end positions for both control points of each line
        end_control_points = []
        for ctrl_pair in start_control_points:
            # Handle both old format (single point) and new format (two points)
            if isinstance(ctrl_pair, list) and len(ctrl_pair) == 2 and isinstance(ctrl_pair[0], list):
                # New format: [ctrl1, ctrl2]
                end_ctrl1 = generate_end_points([ctrl_pair[0]], original_size, original_padding)[0]
                end_ctrl2 = generate_end_points([ctrl_pair[1]], original_size, original_padding)[0]
                end_control_points.append([end_ctrl1, end_ctrl2])
            else:
                # Old format: single control point, convert to two
                old_ctrl = ctrl_pair if isinstance(ctrl_pair, (list, tuple)) else list(ctrl_pair)
                end_ctrl1 = generate_end_points([old_ctrl], original_size, original_padding)[0]
                # Create second control point near the first
                end_ctrl2 = generate_end_points([old_ctrl], original_size, original_padding)[0]
                end_control_points.append([end_ctrl1, end_ctrl2])
    else:
        start_control_points = []
        end_control_points = []
    
    try:
        for frame_num in range(total_frames):
            # Calculate interpolation factor (0 to 1)
            # Use speed to control animation speed
            # Speed is now on a scale where 20.0 = 1.0x baseline
            base_factor = frame_num / (total_frames - 1) if total_frames > 1 else 0
            
            # Normalize speed: 20.0 becomes 1.0x, so divide by 20
            normalized_speed = speed / 20.0
            
            # Colors progress forward continuously through multiple color sets
            # Use linear progression that cycles through color sets for smooth fading
            # Color speed stays the same (not affected by the 10x geometry multiplier)
            color_progress = base_factor * normalized_speed * len(color_sets)
            
            # Find which two color sets to interpolate between
            color_set_index = int(color_progress) % len(color_sets)
            next_color_set_index = (color_set_index + 1) % len(color_sets)
            
            # Get the interpolation factor between the two color sets (0.0 to 1.0)
            color_factor = color_progress % 1.0
            
            # Get the two color sets to interpolate between
            current_color_set = color_sets[color_set_index]
            next_color_set = color_sets[next_color_set_index]
            
            # Geometry movement - 12x faster than colors (smoother than 20x)
            # At higher speeds, geometry moves faster and continues beyond end points (no looping)
            geometry_time = base_factor * normalized_speed * 12.0  # 12x faster than colors (smoother)
            # Don't use modulo - let it continue beyond 1.0 for continuous transformation
            # This makes geometry keep moving in the same direction, creating continuous morphing
            geometry_factor = geometry_time  # Can go beyond 1.0 for continuous transformation
            
            # Interpolate parameters (but keep size constant)
            current_params = interpolate_params(start_params, end_params, geometry_factor)
            # Override size to keep it constant - don't interpolate size
            current_params['size'] = original_size
            current_params['padding'] = original_padding  # Also keep padding constant
            
            # Create modified art_state with interpolated colors and adjusted amount
            modified_state = art_state.copy()
            current_size = original_size  # Always use original size
            current_padding = original_padding  # Always use original padding
            current_amount = int(current_params['amount'])
            
            # Interpolate all colors smoothly between color sets
            # This creates smooth fading transitions without abrupt changes
            modified_state['start_clr'] = [
                int(current_color_set['start_clr'][0] + (next_color_set['start_clr'][0] - current_color_set['start_clr'][0]) * color_factor),
                int(current_color_set['start_clr'][1] + (next_color_set['start_clr'][1] - current_color_set['start_clr'][1]) * color_factor),
                int(current_color_set['start_clr'][2] + (next_color_set['start_clr'][2] - current_color_set['start_clr'][2]) * color_factor)
            ]
            modified_state['end_clr'] = [
                int(current_color_set['end_clr'][0] + (next_color_set['end_clr'][0] - current_color_set['end_clr'][0]) * color_factor),
                int(current_color_set['end_clr'][1] + (next_color_set['end_clr'][1] - current_color_set['end_clr'][1]) * color_factor),
                int(current_color_set['end_clr'][2] + (next_color_set['end_clr'][2] - current_color_set['end_clr'][2]) * color_factor)
            ]
            modified_state['image_bg_clr'] = [
                int(current_color_set['image_bg_clr'][0] + (next_color_set['image_bg_clr'][0] - current_color_set['image_bg_clr'][0]) * color_factor),
                int(current_color_set['image_bg_clr'][1] + (next_color_set['image_bg_clr'][1] - current_color_set['image_bg_clr'][1]) * color_factor),
                int(current_color_set['image_bg_clr'][2] + (next_color_set['image_bg_clr'][2] - current_color_set['image_bg_clr'][2]) * color_factor)
            ]
            modified_state['border_clr'] = [
                int(current_color_set['border_clr'][0] + (next_color_set['border_clr'][0] - current_color_set['border_clr'][0]) * color_factor),
                int(current_color_set['border_clr'][1] + (next_color_set['border_clr'][1] - current_color_set['border_clr'][1]) * color_factor),
                int(current_color_set['border_clr'][2] + (next_color_set['border_clr'][2] - current_color_set['border_clr'][2]) * color_factor)
            ]
            
            # Handle amount changes first
            if current_amount > original_amount:
                # If amount increased, we can't add new points deterministically
                # So we'll just use the original amount
                current_amount = original_amount
            
            # Calculate dynamic zoom based on zoom_speed
            # Zoom oscillates or progresses based on zoom_speed
            import math
            if zoom_speed > 0:
                # Create oscillating zoom effect (zooms in and out)
                zoom_oscillation = math.sin(base_factor * math.pi * 2 * zoom_speed) * 0.3  # Oscillate ±30%
                current_zoom = zoom + zoom_oscillation
                current_zoom = max(0.5, min(2.0, current_zoom))  # Clamp to valid range
            else:
                current_zoom = zoom
            
            # Calculate bounds based on current zoom
            # For zoom < 1.0: constrain to smaller area (more room for movement)
            # For zoom >= 1.0: use full image bounds (zoom in, but still within image)
            image_center = original_size / 2.0
            image_padding = original_padding if original_padding > 0 else 1
            
            if current_zoom < 1.0:
                # Constrain to smaller area
                zoomed_size = original_size * current_zoom
                zoom_offset = (original_size - zoomed_size) / 2.0
                min_bound = max(image_padding, int(zoom_offset))
                max_bound = min(original_size - image_padding - 1, int(original_size - zoom_offset - 1))
            else:
                # Use full image bounds (zoom in, but stay within image)
                min_bound = image_padding
                max_bound = original_size - image_padding - 1
            
            # Animate line points - interpolate from start to end positions with psychedelic effects
            # Only animate the points that will be used (based on current_amount)
            animated_line_points = []
            points_to_use = min(current_amount, len(start_line_points))
            import math
            for i in range(points_to_use):
                start_pt = start_line_points[i]
                end_pt = end_line_points[i]
                # Interpolate position (can go beyond 1.0 for continuous movement)
                animated_x = start_pt[0] + (end_pt[0] - start_pt[0]) * geometry_factor
                animated_y = start_pt[1] + (end_pt[1] - start_pt[1]) * geometry_factor
                
                # Add smooth psychedelic wave distortions to movement
                # Each point gets a unique wave pattern based on its index
                wave_phase = i * 0.3 + geometry_factor * 1.5  # Smoother, slower wave phase
                wave_amplitude = original_size * 0.04  # Reduced amplitude for smoother effect
                wave_x = math.sin(wave_phase) * wave_amplitude
                wave_y = math.cos(wave_phase * 1.2) * wave_amplitude
                
                # Add gentle spiral rotation effect
                rel_to_center_x = animated_x - image_center
                rel_to_center_y = animated_y - image_center
                rotation_angle = geometry_factor * math.pi * 0.2  # Slower rotation (reduced from 0.5)
                rotated_x = rel_to_center_x * math.cos(rotation_angle) - rel_to_center_y * math.sin(rotation_angle)
                rotated_y = rel_to_center_x * math.sin(rotation_angle) + rel_to_center_y * math.cos(rotation_angle)
                
                # Combine base movement with gentle waves and rotation
                psychedelic_x = image_center + rotated_x + wave_x
                psychedelic_y = image_center + rotated_y + wave_y
                
                # Apply zoom: scale around center (using dynamic current_zoom)
                rel_x = psychedelic_x - image_center
                rel_y = psychedelic_y - image_center
                zoomed_x = image_center + rel_x * current_zoom
                zoomed_y = image_center + rel_y * current_zoom
                
                # Clamp to valid image bounds (always within image, never outside)
                # This prevents lines from disappearing
                animated_x = max(min_bound, min(max_bound, int(round(zoomed_x))))
                animated_y = max(min_bound, min(max_bound, int(round(zoomed_y))))
                
                animated_line_points.append([animated_x, animated_y])
            
            modified_state['line_end_points'] = animated_line_points
            
            # Animate curve control points if they exist (now using 2 control points per line)
            if len(start_control_points) > 0:
                animated_control_points = []
                for i in range(points_to_use):
                    if i < len(start_control_points):
                        start_ctrls = start_control_points[i]
                        end_ctrls = end_control_points[i]
                        
                        # Handle both old format (single point) and new format (two points)
                        if isinstance(start_ctrls, list) and len(start_ctrls) == 2 and isinstance(start_ctrls[0], list):
                            # New format: [ctrl1, ctrl2]
                            start_ctrl1 = start_ctrls[0]
                            start_ctrl2 = start_ctrls[1]
                            end_ctrl1 = end_ctrls[0]
                            end_ctrl2 = end_ctrls[1]
                        else:
                            # Old format: single control point, convert to two
                            import random
                            start_ctrl1 = start_ctrls if isinstance(start_ctrls, (list, tuple)) else list(start_ctrls)
                            end_ctrl1 = end_ctrls if isinstance(end_ctrls, (list, tuple)) else list(end_ctrls)
                            # Create second control point near the first
                            start_ctrl2 = [start_ctrl1[0] + random.randint(-30, 30), start_ctrl1[1] + random.randint(-30, 30)]
                            end_ctrl2 = [end_ctrl1[0] + random.randint(-30, 30), end_ctrl1[1] + random.randint(-30, 30)]
                        
                        # Interpolate both control points
                        ctrl1_x = start_ctrl1[0] + (end_ctrl1[0] - start_ctrl1[0]) * geometry_factor
                        ctrl1_y = start_ctrl1[1] + (end_ctrl1[1] - start_ctrl1[1]) * geometry_factor
                        ctrl2_x = start_ctrl2[0] + (end_ctrl2[0] - start_ctrl2[0]) * geometry_factor
                        ctrl2_y = start_ctrl2[1] + (end_ctrl2[1] - start_ctrl2[1]) * geometry_factor
                        
                        # Apply zoom to both control points (using dynamic current_zoom)
                        rel_x1 = ctrl1_x - image_center
                        rel_y1 = ctrl1_y - image_center
                        zoomed_x1 = image_center + rel_x1 * current_zoom
                        zoomed_y1 = image_center + rel_y1 * current_zoom
                        
                        rel_x2 = ctrl2_x - image_center
                        rel_y2 = ctrl2_y - image_center
                        zoomed_x2 = image_center + rel_x2 * current_zoom
                        zoomed_y2 = image_center + rel_y2 * current_zoom
                        
                        # Clamp to bounds
                        animated_control_points.append([
                            [max(min_bound, min(max_bound, int(round(zoomed_x1)))),
                             max(min_bound, min(max_bound, int(round(zoomed_y1))))],
                            [max(min_bound, min(max_bound, int(round(zoomed_x2)))),
                             max(min_bound, min(max_bound, int(round(zoomed_y2))))]
                        ])
                modified_state['curve_control_points'] = animated_control_points
            elif 'curve_control_points' not in art_state:
                # Generate control points if they don't exist (backward compatibility)
                import random
                control_points = []
                for i in range(points_to_use):
                    ctrl1 = [random.randint(min_bound, max_bound), random.randint(min_bound, max_bound)]
                    ctrl2 = [random.randint(min_bound, max_bound), random.randint(min_bound, max_bound)]
                    control_points.append([ctrl1, ctrl2])
                modified_state['curve_control_points'] = control_points
            
            # Animate initial point with zoom and clamping
            animated_x = start_initial_point[0] + (end_initial_point[0] - start_initial_point[0]) * geometry_factor
            animated_y = start_initial_point[1] + (end_initial_point[1] - start_initial_point[1]) * geometry_factor
            
            # Apply zoom (using dynamic current_zoom)
            rel_x = animated_x - image_center
            rel_y = animated_y - image_center
            zoomed_x = image_center + rel_x * current_zoom
            zoomed_y = image_center + rel_y * current_zoom
            
            # Clamp to bounds (always within image)
            animated_initial = [
                max(min_bound, min(max_bound, int(round(zoomed_x)))),
                max(min_bound, min(max_bound, int(round(zoomed_y))))
            ]
            modified_state['initial_point'] = animated_initial
            
            # Handle line_width_variations and line_start_points for current amount
            if current_amount < original_amount:
                modified_state['line_width_variations'] = art_state['line_width_variations'][:current_amount]
                if 'line_start_points' in art_state:
                    modified_state['line_start_points'] = art_state['line_start_points'][:current_amount]
            else:
                modified_state['line_width_variations'] = art_state['line_width_variations']
                if 'line_start_points' in art_state:
                    modified_state['line_start_points'] = art_state['line_start_points']
                elif 'line_start_points' not in modified_state:
                    # Generate branching pattern if not present
                    line_start_points = []
                    for j in range(current_amount):
                        if j == 0:
                            line_start_points.append(None)
                        elif j < current_amount * 0.3:
                            line_start_points.append(random.randint(0, j - 1))
                        else:
                            line_start_points.append(None)
                    modified_state['line_start_points'] = line_start_points
            
            # Generate frame with current parameters and interpolated colors
            frame_result = gen_art(
                current_size,
                current_amount,
                current_params['line_width'],
                current_params['line_width_variation'],
                current_padding,
                current_params['border_width'],
                art_state=modified_state
            )
            
            # Decode base64 image
            img_data = frame_result.split(',')[1]
            img_bytes = base64.b64decode(img_data)
            img = Image.open(BytesIO(img_bytes))
            
            # Resize all frames to the same target size (divisible by 16)
            # This ensures all frames have the same dimensions for video encoding
            if img.size[0] != target_video_size or img.size[1] != target_video_size:
                # Use LANCZOS resampling (PIL.Image.LANCZOS for older versions)
                try:
                    img = img.resize((target_video_size, target_video_size), Image.Resampling.LANCZOS)
                except AttributeError:
                    img = img.resize((target_video_size, target_video_size), Image.LANCZOS)
            
            # Save frame
            frame_path = os.path.join(temp_dir, f"frame_{frame_num:06d}.png")
            img.save(frame_path)
            frames.append(frame_path)
        
        # Create video from frames
        output_path = os.path.join(temp_dir, "output.mp4")
        
        # Ensure temp directory exists
        os.makedirs(temp_dir, exist_ok=True)
        
        # Create video writer (images are already resized to be divisible by 16)
        writer = imageio.get_writer(output_path, fps=fps, codec='libx264', quality=8)
        
        for frame_path in frames:
            if not os.path.exists(frame_path):
                raise FileNotFoundError(f"Frame file not found: {frame_path}")
            frame = imageio.imread(frame_path)
            writer.append_data(frame)
        
        writer.close()
        
        # Wait a moment to ensure file is fully written
        import time
        time.sleep(0.1)
        
        # Verify file exists before reading
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Output video file not found: {output_path}")
        
        # Read video file and convert to base64
        with open(output_path, 'rb') as f:
            video_bytes = f.read()
        
        video_base64 = base64.b64encode(video_bytes).decode('utf-8')
        
        return 'data:video/mp4;base64, ' + video_base64
        
    finally:
        # Clean up temporary files after a short delay to ensure file operations complete
        import time
        import shutil
        time.sleep(0.2)  # Small delay to ensure file operations complete
        shutil.rmtree(temp_dir, ignore_errors=True)
