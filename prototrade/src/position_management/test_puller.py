import random
import time
import signal

# Periodically accesses the shared dictionary
class TestPuller:

   def __init__(self, order_books_dict, order_books_dict_semaphore, test_symbols, strategy_num, stop_event):
      self.order_books_dict = order_books_dict
      self.order_books_dict_semaphore = order_books_dict_semaphore
      self.test_symbols = test_symbols
      self.strategy_num = strategy_num
      self.stop_event = stop_event
     
   def test_pull(self):
      logging.info("TESTS")
      while not self.stop_event.is_set():
         self.order_books_dict_semaphore.acquire()
         symbol = random.choice(self.test_symbols)

         if symbol not in self.order_books_dict:
            self.order_books_dict_semaphore.release()
            logging.info(f"strategy {self.strategy_num} tries to pull, but no quote for {symbol}")
            continue

         quote = self.order_books_dict[symbol]

         self.order_books_dict_semaphore.release()
         
         logging.info(f"strategy {self.strategy_num} pulled: \n{symbol}\n")

         time.sleep(random.uniform(0.1,0.2))
      
      logging.info(f"Positions Manager {self.strategy_num} stopping")