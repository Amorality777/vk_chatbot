#!/url/bin/env python3
import logging.config

import requests
import vk_api
from pony.orm import db_session
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id

import handlers
from log_settings import log_config
from flight_search import flight_search

from models import UserState, Registration

try:
    from settings import GROUP_ID, TOKEN, SCENARIOS, INTENTS, DEFAULT_ANSWER
except ImportError:
    exit('Need to set a token and group id for the bot to work correctly')

logging.config.dictConfig(log_config)
log = logging.getLogger('bot')


class Bot:

    def __init__(self, group_id, token):
        """

        :param group_id: group if from vk.com
        :param token: secret token
        """
        self.group_id = group_id
        self.token = token
        self.vk = vk_api.VkApi(token=self.token)
        self.long_poll = VkBotLongPoll(self.vk, self.group_id)
        self.api = self.vk.get_api()

    def run(self):
        """Run bot"""
        for event in self.long_poll.listen():
            try:
                self.on_event(event=event)
            except Exception as exp:
                log.exception('Error in event handling %s', exp)

    @db_session
    def on_event(self, event):
        """
        Reacts to messages from the user as scripted
        :param event: VkBotMessageEvent object
        :return: None
        """
        if event.type != VkBotEventType.MESSAGE_NEW:
            log.debug("I don't know how to handle this type of event %s", event.type)
            return

        user_id = event.object.peer_id
        text = event.object.text

        state = UserState.get(user_id=str(user_id))
        for intent in INTENTS:
            if any(token in text.lower() for token in intent['tokens']):
                if state is not None:
                    state.delete()
                if intent['answer']:
                    self.send_text(user_id=user_id, text_to_send=intent['answer'])
                else:
                    log.debug('Start scenario %s', intent["scenario"])
                    self.start_scenario(user_id, intent['scenario'], text)
                break
        else:
            if state is not None:
                self.continue_scenario(text, state, user_id)
            else:
                self.send_text(user_id=user_id, text_to_send=DEFAULT_ANSWER)

    def send_text(self, user_id, text_to_send):
        self.api.messages.send(
            peer_id=user_id,
            message=text_to_send,
            random_id=get_random_id()
        )

    def send_image(self, user_id, image):
        upload_url = self.api.photos.getMessagesUploadServer()['upload_url']
        upload_data = requests.post(url=upload_url, files={'photo': ('image.png', image, 'image/png')}).json()
        image_data = self.api.photos.saveMessagesPhoto(**upload_data)
        owner_id = image_data[0]['owner_id']
        media_id = image_data[0]['id']
        attachment = f'photo{owner_id}_{media_id}'
        self.api.messages.send(
            peer_id=user_id,
            attachment=attachment,
            random_id=get_random_id()
        )

    def send_step(self, step, user_id, text, context):
        if 'text' in step:
            self.send_text(user_id=user_id, text_to_send=step['text'].format(**context))
        if 'image' in step:
            handler = getattr(handlers, step['image'])
            image = handler(text, context)
            self.send_image(user_id=user_id, image=image)

    def start_scenario(self, user_id, scenario_name, text):
        scenario = SCENARIOS[scenario_name]
        first_step = scenario['first_step']
        step = scenario['steps'][first_step]
        self.send_step(step, user_id, text, context={})
        UserState(user_id=str(user_id), scenario_name=scenario_name, step_name=first_step, context={})

    def continue_scenario(self, text, state, user_id):
        log.debug('Continue scenario %s', state.scenario_name)
        steps = SCENARIOS[state.scenario_name]['steps']
        step = steps[state.step_name]

        handler = getattr(handlers, step['handler'])

        if handler(text=text, context=state.context):
            next_step = steps[step['next_step']]
            self.send_step(next_step, user_id, text, state.context)
            if next_step['next_step']:
                state.step_name = step['next_step']
            else:
                log.info('Sing up: {phone_number}'.format(**state.context))
                Registration(phone=state.context['phone_number'])
                state.delete()
        else:
            text_to_send = step['failure_text'].format(**state.context)
            self.send_text(user_id=user_id, text_to_send=text_to_send)

        if state.step_name == 'step4':
            text_flights = 'Выберите удобный рейс:\n'
            flights = flight_search(
                from_=state.context['from'],
                to=state.context['to'],
                when=state.context['date']
            )
            state.context['flights'] = flights
            if flights:
                if flights == "date is not current":
                    text_flights = 'На выбранную дату все рейсы уже улетели:)'
                    state.delete()
                else:
                    for num, flight in enumerate(flights):
                        text_flights += f'{num}. {flight}\n'
                self.send_text(user_id, text_flights)
            else:
                text = 'По данному направлению рейсов нет.'
                self.send_text(user_id, text)
                state.delete()

        if state.step_name == 'step7':
            if 'confirmation' in state.context.keys():
                state.delete()
            else:
                flight = int(state.context["flight_number"])
                text_personal_info = f'Город отправления: {state.context["from"]}\n' \
                                     f'Город прибытия: {state.context["to"]}\n' \
                                     f'Информация о рейсе: {state.context["flights"][flight]}\n' \
                                     f'Количество мест: {state.context["number_seats"]}\n' \
                                     f'Дополнительная информация: "{state.context["comment"]}"'
                self.send_text(user_id, text_personal_info)


if __name__ == '__main__':
    try:
        bot = Bot(group_id=GROUP_ID, token=TOKEN)
        bot.run()
    except KeyboardInterrupt:
        log.debug('The program was stopped from the keyboard')
