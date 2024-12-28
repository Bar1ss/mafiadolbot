from .bot import bot
from .database import database


role_titles = {
    'don': 'информатор',
    'mafia': 'мафия',
    'sheriff': 'шериф',
    'peace': 'мирный житель'
}


def stop_game(game, reason):
    bot.try_to_send_message(
        game['chat'],
        f'Игра окончена! {reason}\n\nРоли были распределены следующим образом:\n' +
        '\n'.join([f'{i+1}. {p["name"]} - {role_titles[p.get("role", "?")]}' for i, p in enumerate(game['players'])])
    )
    database.games.delete_one({'_id': game['_id']})