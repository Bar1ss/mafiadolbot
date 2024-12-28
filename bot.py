import config
from .logger import logger
from .database import database

from telebot import TeleBot
from telebot.apihelper import ApiException

TOKEN = '7584993541:AAHJs4bOlEbPtsC8tqDklaSUqT_O1t1TXfc'


def group_only(message):
    return message.chat.type in ('group', 'supergroup')


class MafiaHostBot(TeleBot):
    def try_to_send_message(self, *args, **kwargs):
        try:
            self.send_message(*args, **kwargs)
        except ApiException:
            logger.error('Ошибка API при отправке сообщения', exc_info=True)

    def _game_handler(self, handler):
        def decorator(message, *args, **kwargs):
            game = database.games.find_one({'chat': message.chat.id})
            if game and game['game'] == 'mafia':
                try:
                    player = next(p for p in game['players'] if p['id'] == message.from_user.id)
                except StopIteration:
                    delete = config.DELETE_FROM_EVERYONE and game['stage'] not in (0, -4)
                else:
                    if game['stage'] in (2, 7):
                        victim = game.get('victim')
                        delete = not player.get('alive', True) if victim is None else victim != message.from_user.id
                    else:
                        delete = not player.get('alive', True) or game['stage'] not in (0, -4)
                if delete:
                    self.safely_delete_message(chat_id=message.chat.id, message_id=message.message_id)
                    return

            return handler(message, game, *args, **kwargs)
        return decorator

    def group_message_handler(self, *, func=None, **kwargs):
        def decorator(handler):
            if func is None:
                conjuction = group_only
            else:
                conjuction = lambda message: group_only(message) and func(message)

            new_handler = self._game_handler(handler)
            handler_dict = self._build_handler_dict(new_handler, func=conjuction, **kwargs)
            self.add_message_handler(handler_dict)
            return new_handler
        return decorator

    def safely_delete_message(self, *args, **kwargs):
        try:
            self.delete_message(*args, **kwargs)
        except ApiException:
            logger.debug('Ошибка API при удалении сообщения', exc_info=True)


bot = MafiaHostBot(config.TOKEN, skip_pending=config.SKIP_PENDING)