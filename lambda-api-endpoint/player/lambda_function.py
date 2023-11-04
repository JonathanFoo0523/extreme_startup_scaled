import json
from shared.games_manager import GamesManager
from request_response import *

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

    if req.method == "GET":  # fetch player with <player_id>
        return req.make_response(games_manager.get_game_players(game_id, player_id)[player_id])
    elif (
        req.method == "PUT"
    ):  # update player (change name/api, NOT event management)
        if not (req.is_admin(game_id) or req.is_player(player_id)):
            return UNAUTHORIZED

        if "name" in req.body:
            games_manager.update_player(
                game_id, player_id, name=req.body["name"]
            )

        if "api" in req.body:
            games_manager.update_player(
                game_id, player_id, api=req.body["api"]
            )

        return req.make_response(games_manager.get_game_players(game_id, player_id)[player_id])

    elif req.method == "DELETE":  # delete player with id
        if not (req.is_admin(game_id) or req.is_player(player_id)):
            return UNAUTHORIZED

        games_manager.remove_game_players(game_id, player_id)
        return {"deleted": player_id}
        
    else:
        return METHOD_NOT_ALLOWED
