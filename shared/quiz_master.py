from shared.question_factory import QuestionFactory
from dynamodb.players import Players
from dynamodb.events import Events
from dynamodb.games import Games
import boto3
import requests
import json

dynamodb = boto3.resource('dynamodb')
sqs = boto3.resource('sqs')

PROBLEM_DECREMENT = 50
MIN_REQUEST_INTERVAL_SECS = 1
MAX_REQUEST_INTERVAL_SECS = 20
AVG_REQUEST_INTERVAL = DEFAULT_DELAY = 5
REQUEST_DELTA = 0.1
STREAK_LENGTH = 30

STREAK_MAP = {'ERROR_RESPONSE': '0', 'NO_SERVER_RESPONSE': '0', 'WRONG': 'X', 'CORRECT': '1'}

class QuizMaster:
    def __init__(self):
        self.task_queue = sqs.get_queue_by_name(QueueName='administer_question_tasks')
        self.games = Games(dynamodb)
        self.players = Players(dynamodb)
        self.events = Events(dynamodb)


    # FOR REFERENCE ONLY, NEVER CALLED
    def __create_task_queue(self):
        self.task_queue = sqs.create_queue(QueueName='administer_question_tasks')


    def administer_question(self, game_id, player_id, modification_hash, prev_delay = DEFAULT_DELAY):
        try:
            player = self.players.validate_modification_hash(game_id, player_id, modification_hash)
        except:
            print("Invalid Modification Hash for ", player_id)
            return
        
        player = self.players.get_player(game_id, player_id)
        game = self.games.get_game(game_id)

        # 0. Check if asking question is needed
        if game['ended'] or not player['active']:
            return
        elif not game['running']:
            self.task_queue.send_message(
            MessageBody=json.dumps({
                "game_id": game_id,
                "player_id": player_id,
                "prev_delay": prev_delay,
                "modification_hash": player['modification_hash'],
            }),DelaySeconds=int(prev_delay),)
            return


        # 1. Get Question to ask
        next_question = QuestionFactory().next_question(game['round'])

        # 2. Send Question to player
        try:
            response = requests.get(player["api"], params={"q": next_question.as_text()})
            if response.status_code == 200:
                answer = response.text.strip().lower()
                response_type = ("CORRECT"
                                    if answer == str(next_question.correct_answer()).lower() 
                                    else "WRONG")
            else:
                response_type = "ERROR_RESPONSE"
        except Exception as e:
            response_type = "NO_SERVER_RESPONSE"

        # 3. update Player State
        player_pos = self.player_leaderboard_position(game_id, player_id)
        points_gained = int(self.calculate_points_gained(player_pos, next_question.points, response_type))
        new_score = player['score'] + points_gained
        new_streak = (player['streak'] + STREAK_MAP[response_type])[-STREAK_LENGTH:]
        new_round_index = int(player['round_index'] + 1)
        needs_assistance = self.update_assistance(new_streak[-new_round_index:], player['needs_assistance'])

        self.events.add_event(game_id, player_id, new_score, next_question.as_text(), game['round'], points_gained, response_type)
        
        # new_player_atttibute = {'score': new_score, 'streak': new_streak, 'needs_assistance': needs_assistance}
        new_player_atttibute = {'streak': new_streak, 'needs_assistance': needs_assistance}
        increment = ['round_index', 'request_counts']
        if response_type == 'CORRECT':
            increment.append('correct_tally')
            new_player_atttibute['longest_streak'] = max(self.streak_length(new_streak, '1'), player['longest_streak'])
        else:
            increment.append('incorrect_tally')
        self.players.update_player_attribute(game_id, player_id, increment, **new_player_atttibute)
        self.players.update_score(game_id, player_id, points_gained)

        # 4. Get New Delay
        new_delay = self.delay_before_next_question(prev_delay, response_type)

        # 5. Schedule Next Question
        self.task_queue.send_message(
            MessageBody=json.dumps({
                "game_id": game_id,
                "player_id": player_id,
                "prev_delay": new_delay,
                "modification_hash": player['modification_hash'],
        }),
            DelaySeconds=int(new_delay),
        )


    def calculate_points_gained(self, player_position, question_points, result):
        if result == "CORRECT":
            return question_points
        elif result == "WRONG":
            return -1 * question_points / player_position
        elif result == "ERROR_RESPONSE" or result == "NO_SERVER_RESPONSE":
            return -1 * PROBLEM_DECREMENT
        else:
            raise (f"Error: unrecognized result {result}")


    def player_leaderboard_position(self, game_id, player_id):
        players_by_score = self.players.query_players_by_score(game_id, projection=["player_id"])
        leaderboard = list(map(lambda x: x['player_id'], players_by_score))
        return leaderboard.index(player_id) + 1


    def delay_before_next_question(self, prev_delay, result):
        if result == "CORRECT":
            return max(MIN_REQUEST_INTERVAL_SECS, prev_delay - REQUEST_DELTA)
        elif result == "WRONG":
            return min(MAX_REQUEST_INTERVAL_SECS, prev_delay + REQUEST_DELTA)
        else:
            return 2 * AVG_REQUEST_INTERVAL

    def streak_length(self, response_history, streak_char):
        return len(response_history) - len(response_history.rstrip(streak_char))

    def update_assistance(self, streak, prev):
        need_assistance = self.streak_length(streak, '0X') > 15
        if need_assistance and prev == 2:
            return 2
        elif need_assistance:
            return 1
        else:
            return 0







    # if db_is_game_paused(game_id):
    #     # Put equivalent message on SQS queue again
    #     print("Game is paused. Resending message")
    #     queue.send_message(
    #         MessageBody=json.dumps(sqs_message['body']),
    #         DelaySeconds=20,
    #         MessageAttributes=sqs_message['messageAttributes']
    #     )
    #     return

    # if db_get_game(game_id)['round'] == 1 and player['round_index'] == 0:
    #     # Reset score to 0 once warmup ends, add to running_totals
    #     db_set_player_score(game_id, player_id, 0)
    #     db_set_player_streak(game_id, player_id, "")
    #     db_set_player_correct_tally(game_id, player_id, 0)
    #     db_set_player_incorrect_tally(game_id, player_id, 0)
    #     db_set_request_count(game_id, player_id, 0)
    #     db_add_running_total(game_id, player_id, 0, dt.datetime.now(dt.timezone.utc))
    #     player["score"] = 0
