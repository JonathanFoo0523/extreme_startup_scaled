from uuid import uuid4
from botocore.exceptions import ClientError
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr

class Games:
    def __init__(self, dyn_resource):
        self.dyn_resource = dyn_resource
        self.table = dyn_resource.Table('games')

    # FOR REFERENCE ONLY, NEVER CALLED
    def __create_table(self, table_name='games'):
        try:
            self.table = self.dyn_resource.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'game_id', 'KeyType': 'HASH'},
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'game_id', 'AttributeType': 'S'},
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


    def add_game(self, password):
        item = {
                    'game_id': uuid4().hex[:8],
                    'round': 0,
                    'password': password,
                    'auto_mode': False,
                    'running': True,
                    'ended': False,
                    'modification_hash': uuid4().hex[:6],
                }
        try:
            self.table.put_item(Item=item)
        except ClientError as err:
            print(
                "Couldn't add new game to table %s: %s: %s",
                self.table.name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        return item


    def get_game(self, game_id):
        try:
            response = self.table.get_item(Key={'game_id': game_id})
        except ClientError as err:
            print(
                "Couldn't get game %s from table %s: %s: %s",
                game_id, self.table.name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            
        else:
            return response['Item'] if 'Item' in response else None

    def scan_games(self, projection=[], **eq_filter):
        games = []
        kwargs = {}

        if eq_filter:
            filterExpression = Attr('name').ne("")
            for k, v in eq_filter.items():
                filterExpression = filterExpression & Attr(k).eq(v)
            kwargs['FilterExpression'] = filterExpression

        if projection:
            kwargs['ProjectionExpression'] = ', '.join(map(lambda s : '#' + s, projection))
            kwargs['ExpressionAttributeNames'] = {f'#{s}': s for s in projection}

        try:
            done = False
            start_key = None
            while not done:
                if start_key:
                    kwargs['ExclusiveStartKey'] = start_key
                response = self.table.scan(**kwargs)
                games.extend(response.get('Items', []))
                start_key = response.get('LastEvaluatedKey', None)
                done = start_key is None
        except ClientError as err:
            print(
                "Couldn't scan for games: %s: %s",
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        return games

    def validate_modification_hash(self, game_id, modification_hash):
        try:
            response = self.table.update_item(
                Key={'game_id': game_id},
                UpdateExpression='set modification_hash = :new_hash',
                ConditionExpression="modification_hash = :prev_hash",
                ExpressionAttributeValues={':new_hash' : uuid4().hex[:6], ":prev_hash": modification_hash},
                ReturnValues="UPDATED_NEW")
        except ClientError as err:
            print(
                "Couldn't validate modification_hash for game %s player %s: %s: %s",
                game_id,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            return response['Attributes']

    def update_game_flag(self, game_id, **flag):
        assert len(flag) == 1
        k, v = list(flag.items())[0]

        try:
            response = self.table.update_item(
                Key={'game_id': game_id},
                UpdateExpression=f"set {k}=:b",
                ExpressionAttributeValues={
                    ':b': v},
                ReturnValues="UPDATED_NEW")
        except ClientError as err:
            print(
                "Couldn't update game flag for %s: %s: %s",
                game_id,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            return response['Attributes']

    def update_round(self, game_id, increment=1):
        try:
            response = self.table.update_item(
                Key={'game_id': game_id},
                UpdateExpression="set round = round + :val",
                ExpressionAttributeValues={':val': Decimal(str(increment))},
                ReturnValues="UPDATED_NEW")
        except ClientError as err:
            print(
                "Couldn't increment round for game %s: %s: %s",
                game_id,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            return response['Attributes']

    def update_games_attribute(self, game_id, **attribute):
        expression_values = {f':{k}': v for k, v in attribute.items() }
        expression_names_values = [f'#{k} = :{k}' for k in attribute.keys() ]
        expression_names = {f'#{k}' : k for k in attribute.keys() }

        try:
            response = self.table.update_item(
                Key={'game_id': game_id},
                UpdateExpression='set ' + ",".join(expression_names_values),
                ExpressionAttributeValues=expression_values,
                ExpressionAttributeNames=expression_names,
                ReturnValues="UPDATED_NEW")
        except ClientError as err:
            print(
                "Couldn't update game attribute for game %s: %s: %s",
                game_id,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            return response['Attributes']





    