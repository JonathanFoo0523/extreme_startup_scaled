import json
from shared.games_manager import GamesManager
from request_response import *

def lambda_handler(event, context):
    req = RequestRespond(event)
    games_manager = GamesManager()
    game_id = req.params['game_id']
    
    if not games_manager.game_exists(game_id):
        return NOT_ACCEPTABLE

    if req.method == "GET":
        res = {"authorized": req.is_admin(game_id), "player" : ""}
        if req.get_player()[0]:
            res["player"] = req.get_player()[1]
        return res
        
    elif req.method == "POST":
        if "password" not in req.body:
            return NOT_ACCEPTABLE

        password = req.body["password"]

        if games_manager.game_has_password(game_id, password):
            req.add_admin(game_id)
            return req.make_response({"valid": True})

        return {"valid": False}
        
