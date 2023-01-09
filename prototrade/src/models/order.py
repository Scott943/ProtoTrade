from exceptions.exceptions import InvalidOrderSideException

class Order:
   def __init__(self, symbol, order_side, order_type, volume, price):
      self.symbol = symbol
      self.order_side = order_side
      self.order_type = order_type
      self.volume = volume
      self.price = price

   def __lt__(self, other):
      if self.order_side != other.order_side:
         raise InvalidOrderSideException("Two objects in same heap have different order side types")
      
      if self.order_side == "bid":
         return self.price > other.price # max bid at the top of heap

      return self.price < other.price # min ask at the top of heap

   
