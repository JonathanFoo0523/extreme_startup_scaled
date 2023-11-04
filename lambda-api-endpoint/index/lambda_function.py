import json
from shared.games_manager import GamesManager
from request_response import *

def lambda_handler(event, context):
    req = RequestRespond(event)
    games_manager = GamesManager()
    
    if req.method == "GET":
        return req.make_response(games_manager.get_all_games())

    elif req.method == "POST":
        if "password" not in req.body:
            return NOT_ACCEPTABLE

        new_game = games_manager.new_game(req.body["password"])
        req.add_admin(new_game['game_id'])
        return req.make_response(new_game)

    elif req.method == "DELETE":
        for game in games_manager.get_all_games():
            if req.is_admin(game['game_id']):
                continue
            return UNAUTHORIZED

        games_manager.delete_games()
        return DELETE_SUCCESSFUL
    else:
        return req.make_response("Options", 200)
        