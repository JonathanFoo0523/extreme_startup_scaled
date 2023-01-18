import json
from shared.games_manager import GamesManager
from request_response import *

def lambda_handler(event, context):
    req = RequestRespond(event)
    games_manager = GamesManager()
    game_id = req.params['game_id']
    
    return {"existed": games_manager.game_exists(game_id) and games_manager.review_exists(game_id)}
