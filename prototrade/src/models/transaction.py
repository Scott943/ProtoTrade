

class Transaction:
   def __init__(self, symbol, order_side, order_type, volume, price, timestamp):
      self.symbol = symbol
      self.order_side = order_side
      self.order_type = order_type
      self.volume = volume
      self.price = price
      self.timestamp = timestamp

   
