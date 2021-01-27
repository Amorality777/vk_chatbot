from io import BytesIO

import sys
from PIL import Image, ImageDraw, ImageFont


def generate_ticket(fio: str, from_: str, to: str, date: str):
    background = 'files/ticket_template.png'
    font_file = "files/ofont.ru_Uk_Antique.ttf"
    fill = '#000000'
    try:
        image = Image.open(background)
    except FileNotFoundError:
        print("Unable to load image")
        sys.exit(1)

    fio_coord = (45, 122)
    from_coord = (45, 192)
    to_coord = (45, 258)
    date_coord = (290, 258)

    info = [[fio, fio_coord], [from_, from_coord], [to, to_coord], [date, date_coord]]

    draw = ImageDraw.Draw(image)
    for text, coord in info:
        font = ImageFont.truetype(font_file, size=18)
        draw.text(coord, text, font=font, fill=fill)

    image.save('ticket_example.png')
    temp_file = BytesIO()
    image.save(temp_file, 'png')
    temp_file.seek(0)

    return temp_file

# def generate_ticket(name, email):
#     base = Image.open(TEMPLATE_PATH).convert('RGBA')
#     font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
#
#     draw = ImageDraw.Draw(base)
#     draw.text(NAME_OFFSET, name, font=font, fill=BLACK)
#     draw.text(EMAIL_OFFSET, email, font=font, fill=BLACK)
#
#     response = requests.get(url=f'https://api.adorable.io/avatars/{AVATAR_SIZE}/{email}')
#     avatar_file_like = BytesIO(response.content)
#     avatar = Image.open(avatar_file_like).convert('RGBA')
#
#     base.paste(avatar, AVATAR_OFFSET)
#
#     temp_file = BytesIO()
#     base.save(temp_file, 'png')
#     temp_file.seek(0)
#
#     return temp_file


if __name__ == '__main__':
    generate_ticket(fio='Иван Иванов', from_='Москва', to='Лондон', date='01-01-2021')
