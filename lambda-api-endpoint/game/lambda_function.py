import json
from request_response import *
from shared.games_manager import GamesManager

def lambda_handler(event, context):
    games_manager = GamesManager()
    req = RequestRespond(event)
    game_id = req.params['game_id']
    
    if not games_manager.game_exists(game_id):
        return NOT_ACCEPTABLE

    if req.method == "GET":  
        return req.make_response(games_manager.get_game(game_id))

    elif req.method == "PUT": 
        if not req.is_admin(game_id):
            return UNAUTHORIZED

        if "round" in req.body:  # increment <game_id>'s round by 1
            if games_manager.game_in_last_round(game_id):
                games_manager.delete_games(game_id)
                return req.make_response("GAME_ENDED", 200)

            games_manager.advance_game_round(game_id)
            return req.make_response("ROUND_INCREMENTED", 200)

        elif "pause" in req.body:
            if req.body["pause"]:  # pause <game_id>
                games_manager.pause_game(game_id)  # Kill monitor thread
                return req.make_response("GAME_PAUSED", 200)

            else:  # Unpause the game
                games_manager.unpause_game(game_id)
                return req.make_response("GAME_UNPAUSED", 200)

        elif "auto" in req.body:
            if req.body["auto"]:  # turn on auto mode
                games_manager.set_auto_mode(game_id)
                return req.make_response("GAME_AUTO_ON", 200)
            else:  # turn off auto mode
                games_manager.clear_auto_mode(game_id)
                return req.make_response("GAME_AUTO_OFF", 200)

        elif "end" in req.body:  # End the <game_id> instance
            games_manager.delete_games(game_id)
            return req.make_response("GAME_ENDED", 200)

        elif "assisting" in req.body:
            if games_manager.assist_player(game_id, req.body["assisting"]):
                return req.make_response("ASSISTING {}".format(req.body["assisting"].upper()), 200)
            else:
                return req.make_response("{} not in needs_assistance list".format(req.body["assisting"]), 406)

        return NOT_ACCEPTABLE

    elif req.method == "DELETE":  # delete game with <game_id>
        if not req.is_admin(game_id):
            return UNAUTHORIZED

        games_manager.delete_games(game_id)
        return req.make_response({"deleted": game_id})
        
    else:
        return METHOD_NOT_ALLOWED

