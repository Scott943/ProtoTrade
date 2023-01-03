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
    def __init__(self, streamer_name, streamer_username, streamer_key, exchange_name="iex"):
        self._streamer_name = streamer_name
        self._streamer_username = streamer_username
        self._streamer_key = streamer_key
        self._exchange_name = exchange_name

        self.num_strategies = 0  # This will be incremented when strategies are added
        self._strategy_list = []

    def _create_processes_for_strategies(self):
        # Temporarily ignore SIGINT to prevent interrupts being handled in child processes
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        print(f"Number of strategies: {self.num_strategies}")
        self._strategy_process_pool = Pool(self.num_strategies)

        # Set the handler for SIGINT. Now SIGINT is only handled in the main process
        signal.signal(signal.SIGINT, self._exit_handler)

        print("Creating strategies")

        for strategy in self._strategy_list:  # start readers
            exchange = Exchange(
                self._order_books_dict, self._order_books_dict_semaphore, None)

            self._strategy_process_pool.apply_async(
                strategy.strategy_func, args=(exchange, *strategy.arguments))

        print("Started strategies")

        time.sleep(8)
        self.stop()

    def stop(self):
        # if self.stop_event.set():
        #     return
        print(f"Stopping {current_process().pid}")

        self._stop_event.set()  # Inform child processes to stop
        self._streamer.stop()

        # Prevents any other task from being submitted
        self._strategy_process_pool.close()
        self._strategy_process_pool.join()  # Wait for child processes to finish

        print("Processes terminated")
        exit(1)  # All user work done so can exit

    def _create_shared_memory(self, num_readers):
        manager = Manager()
        shared_dict = manager.dict()
        self._order_books_dict_semaphore = manager.Semaphore(num_readers)
        self._stop_event = manager.Event()

        return shared_dict

    def _exit_handler(self, signum, _):
        if signum == signal.SIGINT:
            self.stop()

    def register_strategy(self, strategy_func, *args):
        self.num_strategies += 1
        self._strategy_list.append(Strategy(strategy_func, args))

    def run_strategies(self):
        self._order_books_dict = self._create_shared_memory(
            self.num_strategies)

        self.price_updater = PriceUpdater(
            self._order_books_dict, self._order_books_dict_semaphore, self.num_strategies, self._stop_event)

        self._streamer = AlpacaDataStreamer(
            self._streamer_username,
            self._streamer_key,
            self.price_updater,
            self._exchange_name
        )

        print("Subscribing to TEST SYMBOLS")

        for symbol in TEST_SYMBOLS:
            self._streamer.subscribe(symbol)
        time.sleep(5)

        self._create_processes_for_strategies()

    def is_running(self):
        return not self._stop_event.is_set()
