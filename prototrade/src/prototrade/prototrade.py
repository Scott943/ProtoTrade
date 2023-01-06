from multiprocessing import Process, Manager, Semaphore, current_process, Pool
from multiprocessing.managers import BaseManager
from ticker_streamer.alpaca_streamer import AlpacaDataStreamer
from ticker_streamer.price_updater import PriceUpdater
from position_management.test_puller import TestPuller
from models.strategy import Strategy
from exchange.exchange import Exchange
from ticker_streamer.subscription_manager import SubscriptionManager
from prototrade.error_processor import ErrorProcessor
from models.error_event import ErrorEvent

import sys
import traceback
import signal
import time

TEST_SYMBOLS = ["AAPL", "GOOG", "MSFT"]

SENTINEL = None


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
                self._order_books_dict, self._order_books_dict_semaphore, None, self._subscription_queue, self._error_queue, strategy_num, self._stop_event)

            res = self._strategy_process_pool.apply_async(
                run_strategy, args=(self._error_queue, strategy.strategy_func, exchange, *strategy.arguments))

        print("Started strategies")
        self._error_processor.join_thread()
        print("Error processing thread joined")

        self.stop()

    def stop(self):
        print("Stopping Program")
        self._stop_event.set()  # Inform child processes to stop
        self._streamer.stop()
        print("Streamer stopped")

        if self._subscription_manager:
            self._subscription_manager.stop_queue_polling()
            print("Subscription manager stopped")

        if not self._error_processor.is_error:
            self._error_processor.stop_queue_polling()
            print("Error processor stopped")

        # Prevents any other task from being submitted
        if self._strategy_process_pool:  # Only close pool if it was opened
            print("Joining processes")
            self._strategy_process_pool.close()
            self._strategy_process_pool.join()  # Wait for child processes to finish
            print("Processes terminated")

        if self._error_processor.is_error:
            print(self._error_processor.exception)

        print("Exiting")
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
                                                         self._subscription_queue, SENTINEL)

        self._error_queue = self.manager.Queue()

        self._error_processor = ErrorProcessor(self._error_queue, SENTINEL)

        print("Creating streamer")

        self._setup_finished = True
        if self._pre_setup_terminate:
            self.stop()  # If CTRL-C pressed while setting up, then trigger stop now

        self._create_processes_for_strategies()

# This has to be outside the class, as otherwise all class members would have to be pickled when sending arguments to the new process


def run_strategy(error_queue, func, exchange, *args):
    try:  # Wrap the user strategy in a try/catch block so we can catch any errors and forward them to the main process
        func(exchange, *args)
    except Exception as e:
        try:
            handle_error(error_queue, e, exchange.exchange_num)
        except Exception as e2:
            print(f"During handling of a strategy error, another error occured: {e2}")
        # At this point the process has finished and can be joined with the main process


def handle_error(error_queue, e, exchange_num):
    exception_info = traceback.format_exc()
    error_queue.put(ErrorEvent(exchange_num, exception_info))
    print(f"Process {exchange_num} EXCEPTION")
