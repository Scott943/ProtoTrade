
class DualHeap:
   def __init__(self):
      self.bid_heap = []
      self.ask_heap = []


   def __repr__(self):
      ret = "Bid Heap\n"
      for x in self.bid_heap:
         ret += str(x) + "\n"

      ret += "Ask Heap \n"
      for x in self.ask_heap:
         ret += str(x) + "\n"

      return ret
   # stores order objects