import eel
import art_gen

@eel.expose
def generate_art(size, amount, line_width, padding, type, border_width):
    return art_gen.gen_art(size, amount, line_width, padding, type, border_width)

eel.init('www')
eel.start('index.html', port = 2000)
