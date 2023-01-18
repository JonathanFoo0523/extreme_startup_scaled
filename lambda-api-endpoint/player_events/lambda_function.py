import json
from shared.games_manager import GamesManager
from request_response import *

## NOT WORKING: "'PlayerEvents' object has no attribute 'query_events_for_player'"

def lambda_handler(event, context):
    req = RequestRespond(event)
    games_manager = GamesManager()
    game_id = req.params['game_id']
    player_id = req.params['player_id']
    
    if not (
        games_manager.game_exists(game_id)
        and games_manager.player_exists(game_id, player_id)
    ):
        return NOT_ACCEPTABLE

    if req.method == "GET":
        return (
            req.make_response({"events": games_manager.get_player_events(game_id, player_id)})
        )
    else:
        return METHOD_NOT_ALLOWED
