import config
from .logger import logger, log_update
from .database import database
from .game import stop_game, role_titles
from .stages import go_to_next_stage
from .bot import bot

import flask
from time import time
from threading import Thread
from telebot.types import Update



def is_game_over(game):
    try:
        alive_players = [p for p in game['players'] if p['alive']]
        mafia = sum(p['role'] in ('don', 'mafia') for p in alive_players)
        return 1 if not mafia else 2 if mafia >= len(alive_players) - mafia else 0
    except KeyError:
        return 0


def stage_cycle():
    while True:
        games_to_modify = database.games.find({'game': 'mafia', 'next_stage_time': {'$lte': time()}})
        for game in games_to_modify:
            game_state = is_game_over(game)
            if game_state:
                role = role_titles['peace' if game_state == 1 else 'mafia']
                for player in game['players']:
                    player_role = player['role'] if player['role'] != 'don' else 'mafia'
                    inc_dict = {'total': 1, f'{player_role}.total': 1}
                    if (
                        (game_state == 1 and player_role != 'mafia') or
                        (game_state == 2 and player_role == 'mafia')
                    ):
                        inc_dict['win'] = 1
                        inc_dict[f'{player_role}.win'] = 1
                    database.stats.update_one(
                        {'id': player['id'], 'chat': game['chat']},
                        {'$set': {'name': player['full_name']}, '$inc': inc_dict},
                        upsert=True
                    )
                stop_game(game, reason=f'Победили игроки команды "{role}"!')
                continue

            game = go_to_next_stage(game)
