import json
from shared.games_manager import GamesManager
from request_response import *

def lambda_handler(event, context):
    req = RequestRespond(event)
    games_manager = GamesManager()
    game_id = req.params['game_id']
    
    if not games_manager.game_exists(game_id):
        return ("Game id not found", NOT_FOUND)
    return req.make_response(games_manager.get_game_running_totals(game_id))