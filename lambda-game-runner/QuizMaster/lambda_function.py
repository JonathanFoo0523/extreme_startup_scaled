from shared.quiz_master import QuizMaster
import json

def lambda_handler(event, context): 
    for record in event['Records']:
        payload = json.loads(record['body'])
        print("Reaceive administering Question task for: ", payload )
        if 'prev_delay' in payload:
            QuizMaster().administer_question(payload["game_id"],
                payload["player_id"], payload["modification_hash"], payload['prev_delay'])
        else:
            QuizMaster().administer_question(payload["game_id"],
                payload["player_id"], payload["modification_hash"])
        return "DONE"