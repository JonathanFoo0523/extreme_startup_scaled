import base64
import json
from decimal import Decimal

NOT_ACCEPTABLE = {'statusCode': 406, 'body': "Unacceptable request - Requested resource not found"}
DELETE_SUCCESSFUL = {'statusCode': 204, 'body': "Successfully deleted"}
METHOD_NOT_ALLOWED = {'statusCode': 405, 'body': "Method Not Allowed"}
UNAUTHORIZED = {'statusCode': 401, 'body': "Unauthenticated request"}

class RequestRespond:
    def __init__(self, payload):
        self.method = payload['requestContext']['http']['method']
        if 'body' in payload:
            self.body = json.loads(payload['body'])
        if 'pathParameters' in payload:
            self.params = payload['pathParameters']
        req_session = None
        if 'cookies' in payload:
            req_session = next((x[len('session='):] for x in payload['cookies'] if x.startswith('session=')), None)
        self.req_session = json.loads(base64.b64decode(req_session).decode('utf-8')) if req_session else {}
        print(self.req_session)
        self.session = {}
        
        
    def make_response(self, body, status=200):
        response = {
            "statusCode": status, 
            "body": JSONSanitizer().encode(body), 
            "headers": {
                "content-type": "application/json",
                "Access-Control-Allow-Headers": "Origin, X-Requested-With, Content-Type, Accept",
                "Access-Control-Allow-Origin": "http://127.0.0.1:5000, https://d1zlib8d3siide.cloudfront.net",
                "Access-Control-Allow-Methods": "POST, PUT, GET, OPTIONS, DELETE",
                "Access-Control-Allow-Credentials": True,
            }
          }
        if self.session:
            session = self.req_session | self.session
            response['cookies'] = ["session=" + base64.b64encode(bytes(json.dumps(session), 'utf-8')).decode() + '; SameSite=None; Secure']
        return response
        
        
    def is_admin(self, game_id):
        return ("admin" in self.req_session) and (game_id in self.req_session["admin"])
        
        
    def add_admin(self, game_id):
        if "admin" in self.req_session:
            self.session["admin"] = self.req_session['admin'] + [game_id]
        else:
            self.session["admin"] = [game_id]
            
    def is_player(self, player_id):
        return ("player" in self.req_session)

    def get_player(self):
        if "player" in self.req_session:
            return True, self.req_session["player"]
        return False, None


class JSONSanitizer(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            if float(obj) % 1 == 0:
                return int(obj)
            return float(obj)
        else:
            return super().default(obj)
