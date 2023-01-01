from multiprocessing import Process, Manager, Semaphore, Pool
from ticker_streamer.ticker_streamer import AlpacaDataStreamer
from ticker_streamer.price_updater import PriceUpdater
from models.positions_manager import PositionsManager
import signal
import time
   
is_stopping = False


def test_execution(positions_managers):
   streamer.subscribe("AAPL")
   streamer.subscribe("MSFT")
   streamer.subscribe("GOOG")
   time.sleep(7)

   for pm in positions_managers: # start readers
      positions_managers_process_pool.apply_async(pm.test_pull)
   print("Started readers")

   time.sleep(8)
   stop_execution()

def stop_execution():
   global is_stopping
   if is_stopping:
      return

   is_stopping = True
   streamer.stop()
   positions_managers_process_pool.terminate()
   print("Processes terminated")
   exit(1)

def handler(signum, _):
   if signum == signal.SIGINT:
      stop_execution()

def create_shared_memory(num_readers):
   global sempahore_access

   manager = Manager()
   shared_dict = manager.dict()
   sempahore_access = Semaphore(num_readers)

   return shared_dict

def main():
   global price_updater
   global streamer
   global positions_managers_process_pool
   
   num_user_strategies = 3

   signal.signal(signal.SIGINT, handler)

   shared_order_books_dict = create_shared_memory(num_user_strategies)

   price_updater = PriceUpdater(
       shared_order_books_dict, sempahore_access, num_user_strategies)

   streamer = AlpacaDataStreamer(
      "AKFA6O7FWKEQ30SFPB9H", 
      "z6Cb3RW4lyp3ykub09tUHjdGF7aNYsGuqXh7WWJs",
      price_updater,
      "iex"
      )

   
   positions_managers_process_pool = Pool(num_user_strategies)
   positions_managers = [] #one per strategy
   test_symbols = ["AAPL", "GOOG", "MSFT"]

   print("Creating readers")
   for i in range(num_user_strategies):
      pm = PositionsManager(shared_order_books_dict, sempahore_access, test_symbols, i)
      positions_managers.append(pm)
      print(f"Created reader {i}")
      

   print("Connection established")
   test_execution(positions_managers)

if __name__ == "__main__":
   main()