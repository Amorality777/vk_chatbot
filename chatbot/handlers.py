import re
from datetime import datetime
from generate_ticket import generate_ticket

try:
    from settings import FLIGHT_CONF
except ImportError:
    exit('You need to load the correct settings')
    FLIGHT_CONF = None

cities_list = tuple(FLIGHT_CONF.keys())
patt_phone_num = re.compile(r'(8 [0-9]{3} [0-9]{3} [0-9]{4})')
patt_name = re.compile(r'^[\w\-\s]{3,30}$')


def handle_name(text, context):
    match = patt_name.match(text)
    if match:
        context['name'] = text
        return True


def is_city(text):
    for city in cities_list:
        if city[1:-1] in text:
            return city


def handle_city_from(text, context):
    city = is_city(text=text)
    if city:
        context['from'] = city
        return True


def handle_city_to(text, context):
    city = is_city(text=text)
    if city:
        context['to'] = city
        return True


def handle_check_date(text, context):
    try:
        datetime.strptime(text, '%d-%m-%Y')
        context['date'] = text
        return True
    except ValueError:
        pass


def handle_choice_flight(text, context):
    try:
        if 0 <= int(text) <= 4:
            context['flight_number'] = int(text)
            return True
    except ValueError:
        pass


def handle_number_seats(text, context):
    try:
        if 0 < int(text) <= 5:
            context['number_seats'] = int(text)
            return True
    except ValueError:
        pass


def handle_comment(text, context):
    context['comment'] = text
    return True


def handle_data_refinement(text, context):
    if text.lower() == 'да':
        context['confirmation'] = 'Yes'
        return True
    else:
        context['confirmation'] = 'No'


def handle_phone_number(text, context):
    phone_num = patt_phone_num.match(text)
    if phone_num:
        context['phone_number'] = phone_num[0]
        return True


def generate_ticket_handler(text, context):
    return generate_ticket(context['name'], context['from'], context['to'], context['date'])
