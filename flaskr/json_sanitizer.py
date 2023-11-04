import json
from decimal import Decimal


class JSONSanitizer(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            if float(obj) % 1 == 0:
                return int(obj)
            return float(obj)
        else:
            return super().default(obj)
        