from uuid import uuid4
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
import datetime as dt


class PlayerEvents:
    def __init__(self, dyn_resource):
        self.dyn_resource = dyn_resource
        self.table = dyn_resource.Table('player_events')


    # FOR REFERENCE ONLY, NEVER CALLED
    def __create_table(self, table_name='player_events'):
        try:
            self.table = self.dyn_resource.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'game_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'player_event_id', 'KeyType': 'RANGE'},
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'game_id', 'AttributeType': 'S'},
                    {'AttributeName': 'player_event_id', 'AttributeType': 'S'}
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


    def add_event(self, game_id, player_id, score, query, difficulty, points_gained, response_type):
        item = {
                    'game_id': game_id,
                    'player_event_id': player_id+uuid4().hex[:8],
                    'score': score,
                    'query': query,
                    'difficulty': difficulty,
                    'points_gained': points_gained,
                    'response_type': response_type,
                    'timestamp': dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
                }
        try:
            self.table.put_item(
                Item=item,
                ReturnValues="ALL_OLD"
                )
        except ClientError as err:
            print(
                "Couldn't add new event to table %s: %s: %s",
                self.table.name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        return item

    def get_event_for_player(self, game_id, player_id, event_id):
        try:
            response = self.table.get_item(Key={'game_id': game_id, 'player_event_id': player_id+event_id})
        except ClientError as err:
            print(
                "Couldn't get player %s from game %s: %s: %s",
                player_id, game_id,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            return response['Item'] if 'Item' in response else None


    def query_events_by_timestamp(self, game_id, projection=[], forward=False, **eq_filter):
        kwargs = {'KeyConditionExpression': Key('game_id').eq(game_id),
                  'IndexName': "timestamp-index",
                  "ScanIndexForward": forward,
                  "ConsistentRead": True}

        if eq_filter:
            filterExpression = Attr('player_event_id').ne("")
            for k, v in eq_filter.items():
                if k == 'player_id':
                    filterExpression = filterExpression & Attr('player_event_id').begins_with(v)
                else:
                    filterExpression = filterExpression & Attr(k).eq(v)
            kwargs['FilterExpression'] = filterExpression

        if projection:
            kwargs['ProjectionExpression'] = ', '.join(map(lambda s : '#' + s, projection))
            kwargs['ExpressionAttributeNames'] = {f'#{s}': s for s in projection}

        try:
            response = self.table.query(**kwargs)
        except ClientError as err:
            print(
                "Couldn't get query events by timestampfrom game %s: %s: %s",
                game_id,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            return response['Items']


    def query_events(self, game_id, projection=[]):
        kwargs = {'KeyConditionExpression': Key('game_id').eq(game_id)}

        if projection:
            kwargs['ProjectionExpression'] = ', '.join(map(lambda s : '#' + s, projection))
            kwargs['ExpressionAttributeNames'] = {f'#{s}': s for s in projection}

        try:
            response = self.table.query(**kwargs)
        except ClientError as err:
            print(
                "Couldn't get event for game %s: %s: %s",
                game_id,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            return response['Items']

