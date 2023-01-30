import prototrade
# help(prototrade)
print("SXX")
from multiprocessing import Process, Manager, Semaphore, current_process, Pool
from multiprocessing.managers import BaseManager, NamespaceProxy
from prototrade.ticker_streamer.alpaca_streamer import AlpacaDataStreamer
from prototrade.ticker_streamer.price_updater import PriceUpdater
from prototrade.models.strategy import Strategy
from prototrade.exchange.exchange import Exchange
from prototrade.ticker_streamer.subscription_manager import SubscriptionManager
from prototrade.error_processor import ErrorProcessor
from prototrade.models.error_event import ErrorEvent
import alpaca_trade_api as tradeapi
from prototrade.exceptions.exceptions import ExchangeNotOpenException

import sys
import traceback
import signal
import time
import logging

TEST_SYMBOLS = ["AAPL", "GOOG", "MSFT"]

SENTINEL = None

logging.basicConfig(level=logging.INFO)

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
        self._rest_api_manager = None
        self._subscription_manager = None
        self._subscription_queue = None
        self._error_queue = None
        self._error_processor = None

        self.num_strategies = 0  # This will be incremented when strategies are added
        self._strategy_list = []

    def _create_processes_for_strategies(self):
        logging.info(f"Number of strategies: {self.num_strategies}")

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

        logging.info("Creating strategy processes")

        # start readers
        for strategy_num, strategy in enumerate(self._strategy_list):
            exchange = Exchange(
                self._order_books_dict, self._order_books_dict_semaphore, self._subscription_queue, self._error_queue, strategy_num, self._stop_event, self._historical_api)
            logging.info("TEST")
            res = self._strategy_process_pool.apply_async(
                run_strategy, args=(self._error_queue, strategy.strategy_func, exchange, *strategy.arguments))
            logging.info(f"Started strategy {strategy_num}")

        logging.info("Started strategies")
        self._error_processor.join_thread()
        logging.info("Error processing thread joined")

        self.stop()

    def stop(self, should_exit=True):
        logging.info("Stopping Program")
        self._stop_event.set()  # Inform child processes to stop
        # logging.info(self._error_processor.exception)
        # Prevents any other task from being submitted
        if self._strategy_process_pool:  # Only close pool if it was opened
            logging.info("Joining processes")
            self._strategy_process_pool.close()
            self._strategy_process_pool.join()  # Wait for child processes to finish
            logging.info("Processes terminated")

        if self._subscription_manager:
            self._subscription_manager.stop_queue_polling()
            logging.info("Subscription manager stopped")

        # Clean up processes before the streamer as processes rely on streamer
        if self._rest_api_manager:
            self._rest_api_manager.shutdown()

        if self._streamer:
            self._streamer.stop()
            logging.info("Streamer stopped")

        if self._error_processor:
            if self._error_processor.is_error:
                logging.info(self._error_processor.exception)
            else:
                self._error_processor.stop_queue_polling()
            logging.info("Error processor stopped")

        if should_exit:
            logging.info("Exiting")
            exit(0)  # All user work done so can exit
        logging.info("No exit in stop()")

    def _create_shared_memory(self, num_readers):
        self.manager = Manager()
        shared_dict = self.manager.dict()
        self._order_books_dict_semaphore = self.manager.Semaphore(num_readers)
        self._stop_event = self.manager.Event()

        return shared_dict

    def _exit_handler(self, signum, _):
        if signum == signal.SIGINT:
            logging.info("\nStopping...")
            if self._setup_finished:
                self.stop()
            else:
                self._pre_setup_terminate = True

    def register_strategy(self, strategy_func, *args):
        self.num_strategies += 1
        self._strategy_list.append(Strategy(strategy_func, args))

    def run_strategies(self):
        try:
            self.create_components() # Try to start all the components and user strategies
        except Exception as e:
            self.stop(False)  # Cleanup then re-raise exception
            raise (e)

    def create_components(self):
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

        if not self._streamer.is_market_open():
            raise ExchangeNotOpenException(
                f"The live exchange is currently closed. Try again during trading hours")

        self.create_shared_rest_api_class()

        self._subscription_queue = self.manager.Queue()

        self._subscription_manager = SubscriptionManager(self._streamer,
                                                         self._subscription_queue, SENTINEL)

        self._error_queue = self.manager.Queue()

        self._error_processor = ErrorProcessor(self._error_queue, SENTINEL)

        logging.info("Creating streamer")

        self._setup_finished = True
        if self._pre_setup_terminate:
            self.stop()  # If CTRL-C pressed while setting up, then trigger stop now

        self._create_processes_for_strategies()

    # This creates a REST api object that is shareable across strategy processes. This means the user can query historical data
    def create_shared_rest_api_class(self):
        CustomManager.register(
            'HistoricalAPI', HistoricalAPI, HistoricalAPIProxy)
        self._rest_api_manager = CustomManager()
        self._rest_api_manager.start()
        rest_api = self._rest_api_manager.HistoricalAPI(
            self._streamer.get_rest_api())  # Pass in the actual rest api as a parameter
        # Get the api object within the class wrapper
        self._historical_api = rest_api.api

# This has to be outside the class, as otherwise all class members would have to be pickled when sending arguments to the new process


def run_strategy(error_queue, func, exchange, *args):
    try:  # Wrap the user strategy in a try/catch block so we can catch any errors and forward them to the main process
        logging.info(f"Running {exchange.exchange_num}")
        func(exchange, *args)
    except Exception as e:
        try:
            handle_error(error_queue, exchange.exchange_num)
        except Exception as e2:
            logging.critical(
                f"During handling of a strategy error, another error occured: {e2}")
        # At this point the process has finished and can be joined with the main process


def handle_error(error_queue, exchange_num):
    logging.error(f"Process {exchange_num} EXCEPTION")
    # Get a string with full original stack trace
    exception_info = traceback.format_exc()
    error_queue.put(ErrorEvent(exchange_num, exception_info))


class CustomManager(BaseManager):
    pass


class HistoricalAPI:
    def __init__(self, api):
        self.api = api  # Holds the api to be used to acquire historical data


class HistoricalAPIProxy(NamespaceProxy):
    # We need to expose the same __dunder__ methods as NamespaceProxy,
    # in addition to the b method.
    _exposed_ = ('__getattribute__', '__setattr__', '__delattr__', 'api')
