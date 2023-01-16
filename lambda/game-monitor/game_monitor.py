from dynamodb.players import Players
from dynamodb.events import Events
from dynamodb.games import Games
from dynamodb.game_events import GameEvents
import boto3
import json
import time
from math import floor, ceil

dynamodb = boto3.resource('dynamodb')
sqs = boto3.resource('sqs')

INCREMENT_ROUND_RATIO_THESHOLD = 0.4
MONITOR_INTERVAL = 2
LEADER_ESTABLISHED_DURATION_REQUIRED = 15
EPIC_COMEBACK_DURATION_REQUIRED = 5

class GameMonitor:
    def __init__(self):
        self.task_queue = sqs.get_queue_by_name(QueueName='game_monitor_tasks')
        self.games = Games(dynamodb)
        self.players = Players(dynamodb)
        self.events = Events(dynamodb)
        self.game_events = GameEvents(dynamodb)

    # FOR REFERENCE ONLY, NEVER CALLED
    def __create_task_queue(self):
        self.task_queue = sqs.create_queue(QueueName='game_monitor_tasks')

    def start(self, game_id, modification_hash):
        self.task_queue.send_message(
            MessageBody=json.dumps({
                "game_id": game_id,
                "type": "AUTO_INCREMENT",
                "modification_hash": modification_hash,
        }))
        self.task_queue.send_message(
            MessageBody=json.dumps({
                "game_id": game_id,
                "type": "EPIC_COMEBACK",
                "potential_players": dict(),
                "transition_players": dict(),
        }))
        self.task_queue.send_message(
            MessageBody=json.dumps({
                "game_id": game_id,
                "type": "NEW_LEADER",
                "prev_leader": None,
                "curr_leader": None,
                "time_in": None,
        }))


    def increment_round_monitor(self, game_id, modification_hash):
        try:
            self.games.validate_modification_hash(game_id, modification_hash)
        except:
            print("Invalid Modification Hash for ")
            return
        
        game = self.games.get_game(game_id)
        if game['ended'] or not game['running'] or not game['auto_mode']:
            return
        elif game['auto_mode'] and game['round'] > 0:
            players = self.players.query_players_by_score(game_id, ["streak"], active=True)
            advancable_players = 0

            for pos, player in enumerate(players):
                streak, round_index = player['streak'], player['round_index']
                round_streak = streak[-round_index:] if round_index != 0 else ""
                c_tail = self.streak_length(round_streak, "1")

                if c_tail >= 6 and pos <= max(0.6 * len(players), 1):
                    advancable_players += 1

            if advancable_players / max(len(players), 1) > INCREMENT_ROUND_RATIO_THESHOLD:
                self.games.update_round(game_id)
                for player in players:
                    self.players.update_player_attribute(game_id, player['player_id'], round_index=0)

        self.task_queue.send_message(
            MessageBody=json.dumps({
                "game_id": game_id,
                "type": "AUTO_INCREMENT",
                "modification_hash": game['modification_hash'],
        }), DelaySeconds=MONITOR_INTERVAL,)

    
    def new_leader_monitor(self, game_id, prev_leader, curr_leader, time_in):
        game = self.games.get_game(game_id)
        if game['ended'] or not game['running']:
            return

        players = self.players.query_players_by_score(game_id, ["player_id", 'name'], active=True)
        if not len(players):
            pass
        elif curr_leader != players[0]['player_id']:
            prev_leader = curr_leader
            curr_leader = players[0]['player_id']
            time_in = time.time()
        elif (
            time.time() - time_in > LEADER_ESTABLISHED_DURATION_REQUIRED
            and prev_leader != curr_leader
        ):
            self.game_events.add_game_events(game_id, "New Leader",
                f"player {players[0]['name']} beat previous leader and maintained that position for more than 15 seconds",
                players[0]['player_id'],
            )
            prev_leader = curr_leader

        self.task_queue.send_message(
            MessageBody=json.dumps({
                "game_id": game_id,
                "type": "NEW_LEADER",
                "prev_leader": prev_leader,
                "curr_leader": curr_leader,
                "time_in": time_in,
        }), DelaySeconds=MONITOR_INTERVAL,)



    def comeback_monitor(self,game_id, potential_players, transition_players):
        game = self.games.get_game(game_id)
        if game['ended'] or not game['running']:
            return
        
        players = self.players.query_players_by_score(game_id, ['player_id', 'name'], active=True)
        bottom_players = self.bottom_20_percentile_players(players)
        top_players = self.top_20_percentile_players(players)
        for pos, player in enumerate(bottom_players):
            pid = player['player_id']
            if pid in potential_players:
                potential_players[pid] = max(pid, pos)
            else:
                potential_players[pid] = pos
        
        for pid, lowest_score in list(potential_players.items()):

            if pid in map(lambda x: x['player_id'], top_players):
                transition_players[pid] = {
                    "worst": lowest_score,
                    "time_in": time.time(),
                }
                del potential_players[pid]

        for pid, entry in list(transition_players.items()):

            if pid not in map(lambda x: x['player_id'], top_players):
                potential_players[pid] = entry["worst"]
                del transition_players[pid]
            elif time.time() - entry["time_in"] > EPIC_COMEBACK_DURATION_REQUIRED:
                player = self.players.get_player(game_id, pid)
                self.game_events.add_game_events(game_id,  "EpicComeback", 
                    f"player {player['name']} started his epic comeback which was at least 5 seconds long",
                    player['player_id']
                )
                del transition_players[pid]

        self.task_queue.send_message(
            MessageBody=json.dumps({
                "game_id": game_id,
                "type": "EPIC_COMEBACK",
                "potential_players": potential_players,
                "transition_players": transition_players,
        }), DelaySeconds=MONITOR_INTERVAL,)


    def streak_length(self, response_history, streak_char):
        return len(response_history) - len(response_history.rstrip(streak_char))

    def top_20_percentile_players(self, ordered_players):
        end_index = floor(len(ordered_players) * 0.2)
        return ordered_players[0:end_index]

    def bottom_20_percentile_players(self, ordered_players):
        from_index = ceil(0.8 * len(ordered_players))
        end_index = len(ordered_players)
        return ordered_players[from_index:end_index]

    