import json
from shared.games_manager import GamesManager
from request_response import *

def lambda_handler(event, context):
    req = RequestRespond(event)
    games_manager = GamesManager()
    game_id = req.params['game_id']
    player_id = req.params['player_id']
    event_id = req.params['event_id']
    
    if not (
        games_manager.game_exists(game_id)
        and games_manager.player_exists(game_id, player_id)
    ):
        return NOT_ACCEPTABLE

    return req.make_response(games_manager.get_player_event(game_id, player_id, event_id))
