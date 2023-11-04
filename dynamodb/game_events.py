from uuid import uuid4
from botocore.exceptions import ClientError
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr
import datetime as dt

class GameEvents:
    def __init__(self, dyn_resource):
        self.dyn_resource = dyn_resource
        self.table = dyn_resource.Table('game_events')

    # FOR REFERENCE ONLY, NEVER CALLED
    def __create_table(self, table_name='game_events'):
        try:
            self.table = self.dyn_resource.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'game_id', 'KeyType': 'HASH'},
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'timestamp', 'AttributeType': 'S'},
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


    def add_game_events(self, game_id, title, description, player_id):
        item = {
                    'game_id': game_id,
                    'timestamp': dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
                    'title': title,
                    'description': description,
                    'player_id': player_id,
                }
        try:
            self.table.put_item(Item=item)
        except ClientError as err:
            print(
                "Couldn't add new game events to table %s: %s: %s",
                self.table.name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        return item


    # def get_game_events(self, game_id):
    #     try:
    #         response = self.table.get_item(Key={'game_id': game_id}, IndexName="game_id-index")
    #     except ClientError as err:
    #         print(
    #             "Couldn't get game events %s from table %s: %s: %s",
    #             game_id, self.table.name,
    #             err.response['Error']['Code'], err.response['Error']['Message'])
            
    #     else:
    #         return response['Item'] if 'Item' in response else None

    def query_game_events_by_timestamp(self, game_id, projection=[], forward=False, **eq_filter):
        kwargs = {'KeyConditionExpression': Key('game_id').eq(game_id),
                  "ScanIndexForward": forward}

        if eq_filter:
            filterExpression = Attr('player_event_id').ne("")
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
                "Couldn't get query game events by timestampfrom game %s: %s: %s",
                game_id,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            return response['Items']

    