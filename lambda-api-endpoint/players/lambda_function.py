import json
from shared.games_manager import GamesManager
from request_response import *

def lambda_handler(event, context):
    req = RequestRespond(event)
    games_manager = GamesManager()
    game_id = req.params['game_id']
    
    if not games_manager.game_exists(game_id):
        return NOT_ACCEPTABLE

    if req.method == "GET":  # fetch all <game_id>'s players
        return req.make_response({"players": games_manager.get_game_players(game_id)})

    elif req.method == "POST":  # create a new player -- initialise thread
        new_player = games_manager.add_player_to_game(
            game_id, req.body["name"], req.body["api"]
        )
        req.session["player"] = new_player["game_id"]

        return req.make_response(new_player)

    elif req.method == "DELETE":
        if not req.is_admin(game_id):
            return UNAUTHORIZED

        games_manager.remove_game_players(game_id)
        return DELETE_SUCCESSFUL
        
    else:
        return METHOD_NOT_ALLOWED
