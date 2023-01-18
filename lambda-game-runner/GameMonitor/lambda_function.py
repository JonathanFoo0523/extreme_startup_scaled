import json
from game_monitor import GameMonitor

def lambda_handler(event, context):
    for record in event['Records']:
        payload = json.loads(record['body'])
        game_id = payload['game_id']
        if payload['type'] == 'START_GAME':
            print("Running START_GAME monitor for: ", game_id)
            GameMonitor().start(game_id, payload['modification_hash'])
        elif payload['type'] == 'AUTO_INCREMENT':
            print("Running AUTO_INCREMENT monitor for: ", game_id)
            GameMonitor().increment_round_monitor(game_id, payload['modification_hash'])
        elif payload['type'] == 'EPIC_COMEBACK':
            print("Running EPIC_COMEBACK monitor for: ", game_id)
            GameMonitor().comeback_monitor(game_id, payload['potential_players'], payload['transition_players'])
        elif payload['type'] == 'NEW_LEADER':
            print("Running NEW_LEADER monitor for: ", game_id)
            GameMonitor().new_leader_monitor(game_id, payload['prev_leader'], payload['curr_leader'], payload['time_in'])
        else:
            raise f"Unknown Payload type: {payload['type']}"