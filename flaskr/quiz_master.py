import time
from flaskr.rate_controller import RateController

# Unique to each player. Responsible for sending questions to user api endpoint at frequency determined by rate_controller
# and incrementing player score in scoreboard
class QuizMaster:
    def __init__(
        self,
        player,
        question_factory,
        scoreboard,
        rlock,
        rate_controller=RateController(),
    ):
        self.player = player
        self.rate_controller = rate_controller
        self.question_factory = question_factory
        self.scoreboard = scoreboard
        self.rlock = rlock
        self.is_warmup = (self.question_factory.round == 0) 

    # Continuous loop, administering questions to self.player at a rate specified by RateController
    def start(self):
        while self.player.active:
            self.administer_question()

    # Administer question involving:
    # (1) acquiring r_lock,
    # (2) send question to user HTTP get,
    # (3) adjust scoreboard/rate_controller based on response
    def administer_question(self):
        if self.is_warmup and self.question_factory.round == 1:
            self.is_warmup = False
            self.reset_scoreboard_and_rc() 

        question = self.question_factory.next_question()

        self.rlock.acquire()  # If wlock acquired (paused), sleep here until wlock released. Many rlock acquires possible for players
        question.ask(self.player)
        if self.rlock.locked():
            self.rlock.release()

        self.scoreboard.record_request_for(self.player)
        self.scoreboard.increment_score_for(self.player, question)
        self.rate_controller.wait_for_next_request(question)
        self.rate_controller = self.rate_controller.update_algorithm_based_on_score(
            self.scoreboard.current_score(self.player)
        )

    def reset_scoreboard_and_rc(self):
        self.scoreboard.reset(self.player)
        self.rate_controller.reset()
    
    def player_passed(self):
        pass
