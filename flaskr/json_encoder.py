import datetime
import json
from flaskr.player import Player
from flaskr.event import Event
from flaskr.game import Game

# Encode application objects to JSON format to support REST api
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Player):
            return dict(
                id=obj.uuid,
                game_id=obj.game_id,
                name=obj.name,
                score=obj.score,
                api=obj.api,
                events=[self.default(e) for e in obj.events],
                streak=obj.streak,
            )
        elif isinstance(obj, Event):
            return dict(
                id=obj.event_id,
                player_id=obj.player_id,
                query=obj.query,
                difficulty=obj.difficulty,
                points_gained=obj.points_gained,
                response_type=obj.response_type,
                timestamp=obj.timestamp,
            )
        elif isinstance(obj, Game):
            return dict(
                id=obj.id, round=obj.round, players=obj.players, paused=obj.paused
            )
        elif isinstance(obj, datetime.datetime):
            return obj.isoformat()

        return super().default(obj)
