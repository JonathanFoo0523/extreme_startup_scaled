import json
import boto3
from shared.question_factory import MAX_ROUND
# from flaskr.json_encoder import JSONEncoder
from dynamodb.games import Games
from dynamodb.players import Players
from dynamodb.player_events import PlayerEvents
from dynamodb.game_events import GameEvents
from uuid import uuid4
# from flaskr.game_stats import GameStats

sqs_client = boto3.client('sqs')
sqs_resource = boto3.resource('sqs')

DEFAULT_DELAY = 5

dynamodb = boto3.resource('dynamodb')
sqs = boto3.resource('sqs')


class AWSGamesManager:
    """ Game manager class for lambda functions and backend server to interface with the DynamoDB """

    def __init__(self):
        try:
            self.administer_question_tasks = sqs_resource.create_queue(QueueName='administer_question_tasks')
        except sqs_client.exceptions.QueueNameExists:
            self.administer_question_tasks = sqs_resource.get_queue_by_name(QueueName='administer_question_tasks')
        except sqs_client.exceptions.QueueDeletedRecently:
            raise

        self.games = Games(dynamodb)
        self.players = Players(dynamodb)
        self.player_events = PlayerEvents(dynamodb)
        self.game_events = GameEvents(dynamodb)
        self.administer_question_queue = sqs.get_queue_by_name(QueueName='administer_question_tasks')
        self.game_monitor_queue = sqs.get_queue_by_name(QueueName='game_monitor_tasks')

    # GAME MANAGEMENT

    def game_exists(self, game_id) -> bool:
        """ Checks if game_id exists in database """
        return self.games.get_game(game_id) is not None

    def get_all_games(self) -> dict:
        """ Returns dict containing all games in the database """
        games = self.games.scan_games(ended=False)
        print(games)
        for i, game in enumerate(games):
            games[i]['players'] = list(map(lambda x: x['player_id'], self.players.query_players(game['game_id'], ['player_id'], active=True)))
        return games

    def get_game(self, game_id) -> dict:
        """ Returns corresponding game for given game_id """
        game = self.games.get_game(game_id)
        players = self.players.query_players(game_id, ['player_id', 'needs_assistance', 'name'], active=True)
        players_ids, being_assisted, needs_assistance = [], [], []
        for player in players:
            players_ids.append(player['player_id'])
            if player['needs_assistance'] == 1:
                needs_assistance.append(player['name'])
            elif player['needs_assistance'] == 2:
                being_assisted.append(player['name'])
        game['players'] = players_ids
        game['players_to_assist'] = {'being_assisted': being_assisted, 'needs_assistance': needs_assistance}
        game['max_round'] = MAX_ROUND
        return game

    def new_game(self, password) -> dict:
        """ Creates a new game in the database and returns newly created <game_id>"""
        assert password.strip() != ""

        game = self.games.add_game(password)

        self.game_monitor_queue.send_message(
            MessageBody=json.dumps({
                "game_id": game['game_id'],
                "type": "START_GAME",
                "modification_hash": game["modification_hash"],
        }),
            DelaySeconds=0,
        )

        return game

    def game_ended(self, game_id) -> bool:
        """ returns True if game has ended, False if not """
        return self.games.get_game(game_id)['ended']

    def game_has_password(self, game_id, password) -> bool:
        """ Checks that game password equals given password """
        return self.games.get_game(game_id)['password'] == password

    def game_in_last_round(self, game_id) -> bool:
        """ Check if game is in its final round """
        return self.games.get_game(game_id)['round'] == MAX_ROUND

    def advance_game_round(self, game_id):
        """ Advances game round """
        game = self.games.update_round(game_id)
        players = self.players.query_players(game_id, ['player_id'], active=True)
        for player in players:
            attributes = {'round_index': 0}
            if game['round'] == 1:
                attributes['streak'] = ""
                attributes['correct_tally'] = attributes['incorrect_tally'] = 0
                attributes['request_counts'] = attributes['score'] = 0
                self.player_events.add_event(game_id, player['player_id'], 0, "WARMUP_ENDED", 1, 0, "")
                attributes['modification_hash'] = uuid4().hex[:6]
                self.players.update_player_attribute(game_id, player['player_id'], **attributes)
                self.administer_question_queue.send_message(
                    MessageBody=json.dumps({
                        "game_id": game_id,
                        "player_id": player['player_id'],
                        "modification_hash": attributes['modification_hash'],
                }), DelaySeconds=0,)
            else:
                self.players.update_player_attribute(game_id, player['player_id'], **attributes)


    def pause_game(self, game_id):
        """ Pause a game """
        self.games.update_games_attribute(game_id, running=False)

    def unpause_game(self, game_id):
        """ Unpause a game """
        game = self.games.get_game(game_id)
        self.games.update_games_attribute(game_id, running=True)
        self.game_monitor_queue.send_message(
            MessageBody=json.dumps({
                "game_id": game_id,
                "type": "START_GAME",
                "modification_hash": game['modification_hash']
        }),
            DelaySeconds=0,
        )

    def end_game(self, game_id):
        """ Ends a game """
        self.games.update_games_attribute(game_id, ended=True)

    def set_auto_mode(self, game_id):
        """ Turns on auto advance round """
        self.games.update_games_attribute(game_id, auto_mode=True)
        game = self.games.get_game(game_id)
        self.game_monitor_queue.send_message(
            MessageBody=json.dumps({
                "game_id": game_id,
                "type": "AUTO_INCREMENT",
                "modification_hash": game['modification_hash']
        }),
            DelaySeconds=0,
        )

    def clear_auto_mode(self, game_id):
        """ Turns off auto advance round """
        self.games.update_games_attribute(game_id, auto_mode=False)

    # PLAYER MANAGEMENT

    def get_game_players(self, game_id, *player_id) -> dict:
        """ If player_id(s) given, returns Player objects for only those players, 
            else returns all Player objects """
        if player_id:
            temp = {}
            for pid in list(player_id):
                temp[pid] =  self.players.get_player(game_id, pid)
                events = self.player_events.query_events_by_timestamp(game_id, player_id=pid)
                for event in events:
                    event['player_id'] = event['player_event_id'][:8]
                    event['event_id'] = event['player_event_id'][8:]
                temp[pid]['events']= events
            return temp
        else:
            players = self.players.query_players(game_id, active=True)
            for player in players:
                events = self.player_events.query_events_by_timestamp(game_id, player_id=player['player_id'])
                for event in events:
                    event['player_id'] = event['player_event_id'][:8]
                    event['event_id'] = event['player_event_id'][8:]
                player['events']= events
            return players

    def player_exists(self, game_id, player_id) -> bool:
        """ Checks if player_id exists in the given game """
        return self.players.get_player(game_id, player_id) is not None


    def get_game_running_totals(self, game_id) -> list:
        """ Gets list of objects in the form {"time": timestamp, "pid": score} """
        game_events = self.player_events.query_events_by_timestamp(game_id, projection=['timestamp', 'player_event_id', 'score'], forward=True)
        ls = [ {"time": event['timestamp'], event['player_event_id'][:8]: event['score']} for event in game_events]
        ls.insert(0, {'time': ls[0]['time']})
        return ls

    def get_score_for_player(self, game_id, player_id) -> int:
        # This function is unused as far as I can see
        """ Returns a player's score """
        return self.players.get_player(game_id, player_id)['score']

    def add_player_to_game(self, game_id, name, api) -> dict:
        """ Adds a player to a game and returns newly added player """
        new_player = self.players.add_player(game_id, name, api)

        self.administer_question_queue.send_message(
            MessageBody=json.dumps({
                "game_id": game_id,
                "player_id": new_player['player_id'],
                "modification_hash": new_player['modification_hash'],
        }),
            DelaySeconds=0,
        )

        return new_player

    def get_players_to_assist(self, game_id) -> dict:
        """ Returns names of players to assist in the form { "needs_assistance": [], "being_assisted": [] } """
        needs_assistance = self.players.query_players(game_id, projection=['name'], needs_assistance=1)
        being_assisted = self.players.query_players(game_id, projection=['name'], needs_assistance=2)
        return { "needs_assistance": list(map(lambda x: x['name'], needs_assistance)), 
                "being_assisted": list(map(lambda x: x['name'], being_assisted)) } 


    def assist_player(self, game_id, player_name):
        """ Updates a player's state from 'needing assistance' to 'being assisted' """
        players = self.players.query_players(game_id, name=player_name)
        if not len(players):
            return False
        
        assert players[0]['needs_assistance'] == 1

        self.players.update_player_attribute(game_id, players[0]['player_id'], needs_assistance=2)
        return True


    def update_player(self, game_id, player_id, name=None, api=None):
        """ Updates name and api of player """
        attribute = {}
        if name:
            attribute['name'] = name
        if api:
            attribute['api'] = api

        self.players.update_player_attribute(game_id, player_id, **attribute)


    def get_player_events(self, game_id, player_id) -> list:
        """ Returns list of event objects for a player """
        return self.player_events.query_events_for_player(game_id, player_id)

    def get_player_event(self, game_id, player_id, event_id) -> list:
        """ Returns list of event objects for a player """
        return self.player_events.get_event_for_player(game_id, player_id, event_id)


    # SIGNATURE CHANGE: FROM *player_id
    def remove_game_players(self, game_id, player_id=None):
        """ If player_id(s) provded, deletes corresponding players, else deletes all players for a given game """
        if player_id:
            self.players.update_player_attribute(game_id, player_id, active=False)
        else:
            players_id = list(map(lambda x: x['player_id'], self.players.query_players(game_id)))
            for pid in players_id:
                self.players.update_player_attribute(game_id, pid, active=False)


    # Methods used after game is ended
    def delete_games(self, *game_id):
        """ If game_id(s) provided, deletes those games, else deletes all games """
        if game_id:
            gids = game_id
        else:
            gids = map(lambda x: x['game_id'], self.games.scan_games(['game_id'], ended=False))

        for gid in list(gids):
            # this will stop all game_monitor and administer_question task
            self.games.update_games_attribute(gid, ended=True, stat=GAME_STAT_PROTOTYPE)
            print("deleted game ", gid)
            

    def review_exists(self, game_id):
        game = self.games.get_game(game_id)
        return game['ended']

    def review_finalboard(self, game_id):
        players = self.players.query_players_by_score(game_id,
            ['player_id', 'name', 'score', 'longest_streak', 'correct_tally', 'request_counts'])
        for player in players:
            if player['request_counts'] > 0:
                player['success_ratio'] = (player['correct_tally'] / player['request_counts'])
            else:
                player['success_ratio'] = 0
        return players

    def review_stats(self, game_id):
        return self.games.get_game(game_id)['stat']

    def review_analysis(self, game_id):
        return self.game_events.query_game_events_by_timestamp(game_id)


GAME_STAT_PROTOTYPE = {
    "total_requests": 0,
    "average_streak": 1,
    "average_on_fire_duration": 0,
    "longest_on_fire_duration": {
        "achieved_by_team": "John",
        "value": 27,
    },
    "longest_streak": 10,
    "average_success_rate": 5,
    "best_success_rate": {
        "achieved_by_team": "John",
        "value": 3,
        },
    "most_epic_comeback": {
        "achieved_by_team": "John",
        "points_gained_during_that_streak": 2,
        "duration": 3,
        "start_position": 10,
        "final_achieved_position": 1,
    },
    "most_epic_fail": {
        "achieved_by_team": "Osc",
        "points_lost_during_that_streak": 3,
        "duration": 2,
        "start_position": 3,
        "final_achieved_position": 20
    },
    "avg_time_to_solve_new_question": [2, 4, 6, 8, 9],
    "time_per_round": [1, 3, 5, 7]
}
