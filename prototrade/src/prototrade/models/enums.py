class OrderType:
   """The order type (used when creating orders)"""
   MARKET = 1
   LIMIT = 2
   FOK = 3

class OrderSide:
   """The side of the order book to place the order in"""
   BID = 1
   ASK = 2

class MarketDataSource:
   ALPACA = 1
   SIMULATED = 2

