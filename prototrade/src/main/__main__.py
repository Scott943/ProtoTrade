from multiprocessing import Process, Manager
from ticker_streamer.ticker_streamer import AlpacaDataStreamer
import signal
import time


def main():
   global streamer

   signal.signal(signal.SIGINT, handler)

   manager = Manager()
   shared_order_books_dict = manager.dict()

   streamer = AlpacaDataStreamer("AKFA6O7FWKEQ30SFPB9H", "z6Cb3RW4lyp3ykub09tUHjdGF7aNYsGuqXh7WWJs", shared_order_books_dict, "iex")
   print("Connection established")
   test_execution(shared_order_books_dict)
   

def test_execution(shared_order_books_dict):
   streamer.subscribe("AAPL")
   time.sleep(5)
   streamer.unsubscribe("AAPL")
   streamer.subscribe("GOOG")

   time.sleep(3)
   streamer.stop()

   time.sleep(2)
   for symbol, book in shared_order_books_dict.items():
      print(symbol)
      print(book)
      print()



def handler(signum, _):
   if signum == signal.SIGINT:
      streamer.stop()
      exit(1)
 

if __name__ == "__main__":
   main()