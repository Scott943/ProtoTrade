import random
import time

# Periodically accesses the shared dictionary
class PositionsManager:

   def __init__(self, order_books_dict, order_books_dict_semaphore, test_symbols, strategy_num):
      self.order_books_dict = order_books_dict
      self.order_books_dict_semaphore = order_books_dict_semaphore
      self.test_symbols = test_symbols
      self.strategy_num = strategy_num
   
   def test_pull(self):
      while True:
         time.sleep(random.uniform(0.1,0.2))
         self.order_books_dict_semaphore.acquire()
         symbol = random.choice(self.test_symbols)
         book = self.order_books_dict[symbol]

         self.order_books_dict_semaphore.release()
         
         print(f"strategy {self.strategy_num} pulled: \n{symbol}\n")
