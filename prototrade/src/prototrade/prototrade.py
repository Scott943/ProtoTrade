from multiprocessing import Process, Manager, Semaphore, current_process, Pool
from multiprocessing.managers import BaseManager
from ticker_streamer.alpaca_streamer import AlpacaDataStreamer
from ticker_streamer.price_updater import PriceUpdater
from position_management.test_puller import TestPuller
from models.strategy import Strategy
from exchange.exchange import Exchange
from ticker_streamer.subscription_manager import SubscriptionManager
import signal
import time

TEST_SYMBOLS = ["AAPL", "GOOG", "MSFT"]


class ProtoTrade:

    # this should be initialised with alpaca credentials and exchange. then register_strategy sued to calculate the num_strategiegs
    def __init__(self, streamer_name, streamer_username, streamer_key, exchange_name="iex"):
        signal.signal(signal.SIGINT, self._exit_handler)
        self._streamer_name = streamer_name
        self._streamer_username = streamer_username
        self._streamer_key = streamer_key
        self._exchange_name = exchange_name

        self._pre_setup_terminate = False
        self._setup_finished = False

        self._streamer = None
        self._stop_event = None
        self._strategy_process_pool = None

        self.num_strategies = 0  # This will be incremented when strategies are added
        self._strategy_list = []


    def _create_processes_for_strategies(self):
        print(f"Number of strategies: {self.num_strategies}")

        # Temporarily ignore SIGINT to prevent interrupts being handled in child processes
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        # SIGINT ignored to set child processes so wrap pool creation in a try except
        try:
            self._strategy_process_pool = Pool(
                self.num_strategies)  # USE SPAWN HERE? Check bloat
        except KeyboardInterrupt:
            self.stop()

        # Set the handler for SIGINT. Now SIGINT is only handled in the main process
        signal.signal(signal.SIGINT, self._exit_handler)

        print("Creating strategy processes")

        # start readers
        for strategy_num, strategy in enumerate(self._strategy_list):

            exchange = Exchange(
                self._order_books_dict, self._order_books_dict_semaphore, None, self._subscription_queue, strategy_num, self._stop_event)

            res = self._strategy_process_pool.apply_async(
                strategy.strategy_func, args=(exchange, *strategy.arguments))

        print("Started strategies")

        time.sleep(8)
        self.stop()

    def stop(self):
        self._stop_event.set()  # Inform child processes to stop
        self._streamer.stop()

        if self._subscription_manager:
            self._subscription_manager.stop_queue_polling()

        # Prevents any other task from being submitted
        if self._strategy_process_pool:  # Only close pool if it was opened
            print("Joining processes")
            self._strategy_process_pool.close()
            self._strategy_process_pool.join()  # Wait for child processes to finish
            print("Processes terminated")

        print("Processes not started yet")
        exit(1)  # All user work done so can exit

    def _create_shared_memory(self, num_readers):
        self.manager = Manager()
        shared_dict = self.manager.dict()
        self._order_books_dict_semaphore = self.manager.Semaphore(num_readers)
        self._stop_event = self.manager.Event()

        return shared_dict

    def _exit_handler(self, signum, _):
        if signum == signal.SIGINT:
            print("\nStopping...")
            if self._setup_finished:
                self.stop()
            else:
                self._pre_setup_terminate = True

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

        self._subscription_queue = self.manager.Queue()

        self._subscription_manager = SubscriptionManager(self._streamer,
                                                         self._subscription_queue)

        print("Creating streamer")

        self._setup_finished = True
        if self._pre_setup_terminate:
            self.stop()  # If CTRL-C pressed while setting up, then trigger stop now

        self._create_processes_for_strategies()

