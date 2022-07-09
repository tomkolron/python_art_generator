import eel
from PIL import Image, ImageDraw
import random
from colorsys import rgb_to_hsv, hsv_to_rgb
from math import sqrt
from subprocess import Popen, PIPE, CalledProcessError
import base64
from io import BytesIO

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

@eel.expose
def gen_art(size, amount, line_width, padding, type, border_width):
    size = int(size)
    amount = int(amount)
    line_width = int(line_width)
    padding = int(padding)
    type = int(type)
    border_width = int(border_width)
    colors = []
    image_size = size
    if padding > 0:
        image_padding = padding
    else:
        image_padding = 1
    start_clr = rand_clr(colors)
    colors.append(start_clr)
    end_clr = rand_clr(colors)
    colors.append(start_clr)
    image_bg_clr = rand_clr(colors)
    colors.append(image_bg_clr)
    border_clr = rand_clr(colors)
    colors.append(image_bg_clr)
    image = Image.new('RGB', (image_size, image_size), image_bg_clr)
   
    #Draw interface
    draw = ImageDraw.Draw(image)

    #Draw border
    draw.rectangle((0, 0, image_size - 1, image_size - 1), outline=border_clr, width=border_width)

    #Draw lines
    line_amount = amount
    last_point = (random.randint(image_padding, image_size - image_padding), random.randint(image_padding, image_size - image_padding))
    center_point = ((image_size / 2) - 1,(image_size / 2) - 1)
    counter = 0
    for i in range(line_amount):
        if type == 1:
            rand_x = last_point
        else:
            rand_x = center_point
        rand_y = (random.randint(image_padding, image_size - image_padding), random.randint(image_padding, image_size - image_padding))

        line_cords = (rand_x, rand_y)
        line_color = interpolate(start_clr, end_clr, i / (line_amount - 1))
       
        draw.line(line_cords, line_color, line_width)
        last_point = rand_y
   

    #return Image
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return 'data:image/png;base64, ' + img_str

# if __name__ == "__main__":
#     print('Generating art:')
#     size = 64
#     line_amount = 200
#     line_width = 1
#     padding = 3
#     type = 2
#     border_width = 1
#     for i in range(1):
#         gen_art(size, line_amount, line_width, padding, type, border_width)

eel.init('www')
eel.start('index.html')
