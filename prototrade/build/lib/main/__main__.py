from multiprocessing import Process, Manager, Semaphore
from ticker_streamer.ticker_streamer import AlpacaDataStreamer
from models.positions_manager import PositionsManager
import signal
import time
   

def test_execution(shared_order_books_dict, positions_managers_processes):
   streamer.subscribe("AAPL")
   streamer.subscribe("MSFT")
   streamer.subscribe("GOOG")
   time.sleep(6)

   for pm in positions_managers_processes: #start readers
      pm.start()
   print("Started readers")

   time.sleep(8)
   streamer.stop()

def handler(signum, _):
   if signum == signal.SIGINT:
      streamer.stop()
      for p in positions_managers_processes:
         p.terminate()
      exit(1)

def create_shared_memory(num_readers):
   global sempahore_access

   manager = Manager()
   shared_dict = manager.dict()
   sempahore_access = Semaphore(num_readers)

   return shared_dict

def main():
   global streamer
   num_user_strategies = 3

   signal.signal(signal.SIGINT, handler)

   shared_order_books_dict = create_shared_memory(num_user_strategies)

   streamer = AlpacaDataStreamer(
      "AKFA6O7FWKEQ30SFPB9H", 
      "z6Cb3RW4lyp3ykub09tUHjdGF7aNYsGuqXh7WWJs", 
      "iex"
      )

   global positions_managers_processes
   positions_managers_processes = []
   positions_managers = [] #one per strategy
   test_symbols = ["AAPL", "GOOG", "MSFT"]

   print("Creating readers")
   for i in range(num_user_strategies):
      pm = PositionsManager(shared_order_books_dict, sempahore_access, test_symbols, i)
      positions_managers.append(pm)
      positions_managers_processes.append(Process(target=pm.test_pull))
      print(f"Created reader {i}")
      

   print("Connection established")
   test_execution(shared_order_books_dict, positions_managers_processes)

if __name__ == "__main__":
   main()