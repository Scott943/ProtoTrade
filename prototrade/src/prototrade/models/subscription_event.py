from enum import Enum

class SubscriptionEvent:
    def __init__(self, symbol, event_type, strategy_num):
        self.symbol = symbol
        self.event_type = event_type
        self.strategy_num = strategy_num


class SubscribeType(Enum):
    SUBSCRIBE = 1
    UNSUBSCRIBE = 2