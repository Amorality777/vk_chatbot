import datetime
from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch, Mock

from pony.orm import db_session, rollback
from vk_api.bot_longpoll import VkBotMessageEvent

import settings
from bot import Bot
from generate_ticket import generate_ticket
from flight_search import flight_search

DATE = str(datetime.date.today().strftime('%d-%m-%Y'))


def isolate_db(test_func):
    def wrapper(*args, **kwargs):
        with db_session():
            test_func(*args, **kwargs)
            rollback()

    return wrapper


def generate_flights():
    text_flights = 'Выберите удобный рейс:\n'
    flights = flight_search(
        from_='Москва',
        to='Вашингтон',
        when=DATE
    )
    for num, flight in enumerate(flights):
        text_flights += f'{num}. {flight}\n'
    return text_flights


class TestBot(TestCase):
    RAW_EVENT = {'type': 'message_new',
                 'object': {'date': 1593850615, 'from_id': 91101376, 'id': 85, 'out': 0, 'peer_id': 91101376,
                            'text': 'some text',
                            'conversation_message_id': 77, 'fwd_messages': [], 'important': False, 'random_id': 0,
                            'attachments': [],
                            'is_hidden': False}, 'group_id': 196748767,
                 'event_id': 'fbc174593af2f8513b0e24fa1c2d5a6402ccaa3d'}

    def test_run(self):
        count = 5
        obj = {}
        events = [obj] * count
        long_poller_mock = Mock(return_value=events)
        long_poller_listen_mock = Mock()
        long_poller_listen_mock.listen = long_poller_mock

        with patch('bot.vk_api.VkApi'):
            with patch('bot.VkBotLongPoll', return_value=long_poller_listen_mock):
                bot = Bot('', '')
                bot.on_event = Mock()
                bot.run()

                bot.on_event.assert_called()
                bot.on_event.assert_any_call(event=obj)
                self.assertEqual(bot.on_event.call_count, count)

    INPUTS = [
        'Привет!',
        'Который час?',
        'Ввожу /ticket',
        'Иван',
        'москву',
        'Вашингтон',
        '22-22-2020',
        DATE,
        '1',
        '2',
        'комментарий',
        'Да',
        '8 888 888 8888',
        'пока'
    ]
    flights = generate_flights()
    reg = settings.SCENARIOS['registration']['steps']
    EXPECTED_OUTPUTS = [
        settings.INTENTS[0]['answer'],
        settings.DEFAULT_ANSWER,
        reg['step0']['text'],
        reg['step1']['text'],
        reg['step2']['text'],
        reg['step3']['text'],
        reg['step3']['failure_text'],
        reg['step4']['text'],
        flights,
        reg['step5']['text'],
        reg['step6']['text'],
        reg['step7']['text'],
        f'Город отправления: Москва\nГород прибытия: Вашингтон\n'
        f'Информация о рейсе: 14:30 {DATE}\nКоличество мест: 2\nДополнительная информация: "комментарий"',
        reg['step8']['text'],
        reg['step9']['text'],
        settings.INTENTS[3]['answer']
    ]

    @isolate_db
    def test_run_ok(self):
        send_mock = Mock()
        api_mock = Mock()
        api_mock.messages.send = send_mock

        events = []
        for input_text in self.INPUTS:
            event = deepcopy(self.RAW_EVENT)
            event['object']['text'] = input_text
            events.append((VkBotMessageEvent(event)))

        long_poller_mock = Mock()
        long_poller_mock.listen = Mock(return_value=events)

        with patch('bot.VkBotLongPoll', return_value=long_poller_mock):
            bot = Bot('', '')
            bot.api = api_mock
            bot.send_image = Mock()
            bot.run()
        assert send_mock.call_count == len(self.INPUTS) + 2

        real_output = []
        for call in send_mock.call_args_list:
            args, kwargs = call
            real_output.append(kwargs['message'])
        assert real_output == self.EXPECTED_OUTPUTS

    def test_image_generation(self):
        ticket_file = generate_ticket(fio='Иван Иванов', from_='Москва', to='Лондон', date='01-01-2021')
        with open('files/ticket_example.png', 'rb') as expected_file:
            expected_bytes = expected_file.read()
        assert ticket_file.read() == expected_bytes
