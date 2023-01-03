from multiprocessing import Process, Manager, Semaphore, Pool, current_process
from ticker_streamer.alpaca_streamer import AlpacaDataStreamer
from ticker_streamer.price_updater import PriceUpdater
from position_management.test_puller import TestPuller
from models.strategy import Strategy
from exchange.exchange import Exchange
import signal
import time

TEST_SYMBOLS = ["AAPL", "GOOG", "MSFT"]


class ProtoTrade:

    # this should be initialised with alpaca credentials and exchange. then register_strategy sued to calculate the num_strategiegs
    def __init__(self):
        self.num_strategies = 0  # This will be incremented when strategies are added
        self.strategy_list = []

    def _create_processes_for_strategies(self):
        # Temporarily ignore SIGINT to prevent interrupts being handled in child processes
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        print(f"Number of strategies: {self.num_strategies}")
        self.strategy_process_pool = Pool(self.num_strategies)

        # Set the handler for SIGINT. Now SIGINT is only handled in the main process
        signal.signal(signal.SIGINT, self._exit_handler)

        print("Creating strategies")

        for strategy in self.strategy_list:  # start readers
            
            exchange = Exchange(
                self.order_books_dict, self.order_books_dict_semaphore, None)

            res = self.strategy_process_pool.apply_async(
                strategy.strategy_func, args=(exchange, *strategy.arguments))
            res.get()

        print("Started strategies")

        time.sleep(8)
        self.stop()

    def stop(self):
        # if self.stop_event.set():
        #     return
        print(f"Stopping {current_process().pid}")

        self.stop_event.set()  # Inform child processes to stop
        self.streamer.stop()

        self.strategy_process_pool.close()  # Prevents any other task from being submitted
        self.strategy_process_pool.join()  # Wait for child processes to finish

        print("Processes terminated")
        exit(1) # All user work done so can exit

    def _create_shared_memory(self, num_readers):
        manager = Manager()
        shared_dict = manager.dict()
        self.order_books_dict_semaphore = manager.Semaphore(num_readers)
        self.stop_event = manager.Event()

        return shared_dict

    def _exit_handler(self, signum, _):
        if signum == signal.SIGINT:
            self.stop()

    def register_strategy(self, strategy_func, *args):
        self.num_strategies += 1
        self.strategy_list.append(Strategy(strategy_func, args))

    def run_strategies(self):
        self.order_books_dict = self._create_shared_memory(
            self.num_strategies)

        self.price_updater = PriceUpdater(
            self.order_books_dict, self.order_books_dict_semaphore, self.num_strategies, self.stop_event)

        self.streamer = AlpacaDataStreamer(
            "AKFA6O7FWKEQ30SFPB9H",
            "z6Cb3RW4lyp3ykub09tUHjdGF7aNYsGuqXh7WWJs",
            self.price_updater,
            "iex"
        )

        print("Subscribing to TEST SYMBOLS")

        for symbol in TEST_SYMBOLS:
            self.streamer.subscribe(symbol)
        time.sleep(5)

        self._create_processes_for_strategies()

    def is_running(self):
        return not self.stop_event.is_set()