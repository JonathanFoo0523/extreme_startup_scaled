from uuid import uuid4
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal

def sanitize(item):
    if type(item) is list:
        return [sanitize(i) for i in item]
    else:
        return dict(map(lambda x: (x[0], int(x[1])) if isinstance(x[1], Decimal) else x, item))

class Players:
    def __init__(self, dyn_resource):
        self.dyn_resource = dyn_resource
        self.table = dyn_resource.Table('players')


    # FOR REFERENCE ONLY, NEVER CALLED
    def __create_table(self, table_name='players'):
        try:
            self.table = self.dyn_resource.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'game_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'player_id', 'KeyType': 'RANGE'},
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'game_id', 'AttributeType': 'S'},
                    {'AttributeName': 'player_id', 'AttributeType': 'S'}
                ],
                ProvisionedThroughput={'ReadCapacityUnits': 10, 'WriteCapacityUnits': 10})
            self.table.wait_until_exists()
        except ClientError as err:
            print(
                "Couldn't create table %s: %s: %s", table_name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            return self.table


    def add_player(self, game_id, name, api):
        item = {
                    'game_id': game_id,
                    'player_id': uuid4().hex[:8],
                    'name': name,
                    'api': api,
                    'active': True,
                    'score': 0,
                    'streak': '',
                    'round_index': 0,
                    'longest_streak': 0,
                    'correct_tally': 0,
                    'incorrect_tally': 0,
                    'request_counts': 0,
                    'needs_assistance': 0,
                    'modification_hash': uuid4().hex[:6],
                }
        try:
            self.table.put_item(Item=item,ReturnValues="ALL_OLD")
        except ClientError as err:
            print(
                "Couldn't add new player to table %s: %s: %s",
                self.table.name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        return item


    def get_player(self, game_id, player_id):
        try:
            response = self.table.get_item(Key={'game_id': game_id, 'player_id': player_id})
        except ClientError as err:
            print(
                "Couldn't get player %s from game %s: %s: %s",
                player_id, game_id,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            return response['Item'] if 'Item' in response else None


    def query_players(self, game_id, projection=[], **eq_filter):
        kwargs = {'KeyConditionExpression': Key('game_id').eq(game_id)}

        if eq_filter:
            filterExpression = Attr('name').ne("")
            for k, v in eq_filter.items():
                filterExpression = filterExpression & Attr(k).eq(v)
            kwargs['FilterExpression'] = filterExpression

        if projection:
            kwargs['ProjectionExpression'] = ', '.join(map(lambda s : '#' + s, projection))
            kwargs['ExpressionAttributeNames'] = {f'#{s}': s for s in projection}
        
        try:
            response = self.table.query(**kwargs)
        except ClientError as err:
            print(
                "Couldn't query for players from %s: %s: %s", game_id,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            return response['Items']


    # def query_players_id(self, game_id):
    #     try:
    #         response = self.table.query(
    #             ProjectionExpression="player_id",
    #             KeyConditionExpression=Key('game_id').eq(game_id)
    #             )
    #     except ClientError as err:
    #         print(
    #             "Couldn't query for players from %s: %s: %s", game_id,
    #             err.response['Error']['Code'], err.response['Error']['Message'])
    #         raise
    #     else:
    #         return response['Items']

    def query_players_by_score(self, game_id, projection=[], forward=False, **eq_filter):
        kwargs = {'KeyConditionExpression': Key('game_id').eq(game_id),
                  'IndexName': "score-index",
                  "ScanIndexForward": forward,
                  "ConsistentRead": True}

        if eq_filter:
            filterExpression = Attr('name').ne("")
            for k, v in eq_filter.items():
                filterExpression = filterExpression & Attr(k).eq(v)
            kwargs['FilterExpression'] = filterExpression

        if projection:
            kwargs['ProjectionExpression'] = ', '.join(map(lambda s : '#' + s, projection))
            kwargs['ExpressionAttributeNames'] = {f'#{s}': s for s in projection}
        
        try:
            response = self.table.query(**kwargs)
        except ClientError as err:
            print(
                "Couldn't query for players from %s: %s: %s", game_id,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            return response['Items']


    def validate_modification_hash(self, game_id, player_id, modification_hash):
        try:
            response = self.table.update_item(
                Key={'game_id': game_id, 'player_id': player_id},
                UpdateExpression='set modification_hash = :new_hash',
                ConditionExpression="modification_hash = :prev_hash",
                ExpressionAttributeValues={':new_hash' : uuid4().hex[:6], ":prev_hash": modification_hash},
                ReturnValues="UPDATED_NEW")
        except ClientError as err:
            print(
                "Couldn't validate modification_hash for game %s player %s: %s: %s",
                game_id, player_id,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            return response['Attributes']



    def update_player_attribute(self, game_id, player_id, increment=[], **attribute):
        expression_values = {f':{k}': v for k, v in attribute.items() }
        expression_names_values = [f'#{k} = :{k}' for k in attribute.keys() ]
        expression_names = {f'#{k}' : k for k in attribute.keys() }
        update_expression = 'set ' + ",".join(expression_names_values)
        if increment:
            update_expression += ", " + ",".join(map(lambda x: f'{x} = {x} + :one', increment))
            expression_values[':one'] = 1

        try:
            response = self.table.update_item(
                Key={'game_id': game_id, 'player_id': player_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ExpressionAttributeNames=expression_names,
                ReturnValues="UPDATED_NEW")
        except ClientError as err:
            print(
                "Couldn't update player attribute for game %s and player %s: %s: %s",
                game_id, player_id,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            return response['Attributes']


    def update_score(self, game_id, player_id, increment=1):
        try:
            response = self.table.update_item(
                Key={'game_id': game_id, 'player_id': player_id},
                UpdateExpression="set score = score + :val",
                ExpressionAttributeValues={':val': Decimal(str(increment))},
                ReturnValues="UPDATED_NEW")
        except ClientError as err:
            print(
                "Couldn't increment score for game %s for player %s: %s: %s",
                game_id, player_id,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            return response['Attributes']




    


    