import json
from request_response import *
from shared.games_manager import GamesManager

def lambda_handler(event, context):
    req = RequestRespond(event)
    games_manager = GamesManager()
    game_id = req.params['game_id']
    
    if not games_manager.game_exists(game_id):
        return NOT_ACCEPTABLE

    return games_manager.get_game_running_totals(game_id)
