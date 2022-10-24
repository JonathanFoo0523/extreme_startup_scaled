import sys
sys.path.append(".")

from flaskr.rate_controller import RateController
from unittest.mock import Mock
import pytest

DEFAULT_DELAY = 5
AVG_DELAY = 10
DELTA = 0.1

@pytest.fixture()
def basic_rate_controller():
    return RateController(DEFAULT_DELAY)

def test_increases_delay_by_delta_when_incorrect_answer(basic_rate_controller):
    question = Mock()
    question.problem = ""
    question.answered_correctly.return_value = False

    basic_rate_controller.delay_before_next_request(question)
    assert basic_rate_controller.delay == DEFAULT_DELAY + DELTA

def test_decreases_delay_by_delta_when_correct_answer(basic_rate_controller):
    question = Mock()
    question.problem = ""
    question.answered_correctly.return_value = True

    basic_rate_controller.delay_before_next_request(question)
    assert basic_rate_controller.delay == DEFAULT_DELAY - DELTA

def test_sets_delay_to_avg_rate_on_problem_if_current_delay_less_than_avg(basic_rate_controller):
    question = Mock()
    question.problem = "problem_detected"
    question.answered_correctly.return_value = False

    basic_rate_controller.delay_before_next_request(question)
    assert basic_rate_controller.delay == AVG_DELAY


def test_maintains_delay_on_problem_if_current_delay_less_than_avg():
    delayed_controller = RateController(AVG_DELAY + 5)
    question = Mock()
    question.problem = "problem_detected"
    question.answered_correctly.return_value = False

    delayed_controller.delay_before_next_request(question)
    assert delayed_controller.delay == AVG_DELAY + 5

# TODO: Updates algorithm based on score
# TODO: Advanced/specialised RateController(s) tests