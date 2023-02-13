import logging
logging.basicConfig(format='-%(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# logger.getLogger('websockets').setLevel('INFO')

import multiprocessing
from multiprocessing import Manager, Pool, Process
from multiprocessing.managers import BaseManager, NamespaceProxy
from prototrade.ticker_streamer.alpaca_streamer import AlpacaDataStreamer
from prototrade.ticker_streamer.price_updater import PriceUpdater
from prototrade.models.strategy import Strategy
from prototrade.exchange.exchange import Exchange
from prototrade.ticker_streamer.subscription_manager import SubscriptionManager
from prototrade.exceptions.error_processor import ErrorProcessor
from prototrade.models.error_event import ErrorEvent
from prototrade.exceptions.exceptions import ExchangeNotOpenException
from pathlib import Path
from prototrade.file_manager.file_manager import FileManager
from prototrade.models.strategy_file_locks import _StrategyLocks
from prototrade.grapher.grapher import _Grapher

import traceback
import signal


SENTINEL = None

class StrategyRegistry:
    """The master class used for initialising & running the framework. Handles allocating processes to each of the registered strategies.

    :raises ExchangeNotOpenException: If the exchange is currently closed, this error is raised
    """
    # this should be initialised with alpaca credentials and exchange. then register_strategy sued to calculate the num_strategiegs
    def __init__(self, streamer_name, streamer_username, streamer_key, exchange_name="iex", save_data_location = None):
        """Initalise the virtual exchange. This should be done inside a main() function within the user's program.

        :param streamer_name: The name of the streamer to use. Recommended: ``'alpaca'``
        :type streamer_name: str
        :param streamer_username: The API usesrname
        :type streamer_username: str
        :param streamer_key: The corresponding API key
        :type streamer_key: str
        :param exchange_name: The exchange to use. For alpaca, this can be ``sip`` (all US exchanges - paid subscription only) or ``iex``, defaults to "iex"
        :type exchange_name: str, optional
        :param save_data_location: The relative file location (from the user strategy script) to save data about each run, defaults to None
        :type save_data_location: str, optional
        """
        
        signal.signal(signal.SIGINT, self._exit_handler)
        self._streamer_name = streamer_name
        self._streamer_username = streamer_username
        self._streamer_key = streamer_key
        self._exchange_name = exchange_name

        if save_data_location:
            self.save_data_location = Path(save_data_location).resolve()
        else:
            self.save_data_location = Path('.').resolve()

        self._pre_setup_terminate = False
        self._setup_finished = False

        self._streamer = None
        self._stop_event = None
        self._strategy_process_pool = None
        self._custom_obj_manager = None
        self._subscription_manager = None
        self._subscription_queue = None
        self._error_queue = None
        self._error_processor = None
        self._file_manager = None
        self._graphing_process = None

        self.num_strategies = 0  # This will be incremented when strategies are added
        self._strategy_list = []
        self._file_locks = []

    def _create_processes_for_strategies(self):
        logger.info(f"Number of strategies: {self.num_strategies}")

        # Temporarily ignore SIGINT to prevent interrupts being handled in child processes
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        # SIGINT ignored to set child processes so wrap pool creation in a try except

        # Windows only supports spawning processes (instead of forking), so design design has been taking to always spawn regardless of operating system
        try:
            self._strategy_process_pool = multiprocessing.get_context('spawn').Pool(
                self.num_strategies + 1)  # USE SPAWN HERE? Check bloat
        except KeyboardInterrupt:
            self._stop()

        # Set the handler for SIGINT. Now SIGINT is only handled in the main process
        signal.signal(signal.SIGINT, self._exit_handler)

        logger.debug("Creating strategy processes")

        self.create_file_locks()
        self._file_manager = FileManager(self.save_data_location, self.num_strategies, self._file_locks)
        
        self._graphing_process = Process(target = create_grapher, args=(self._error_queue, self._stop_event, self._file_manager, self._file_locks, self.num_strategies,))
        self._graphing_process.start()

        for strategy_num, strategy in enumerate(self._strategy_list):
            save_data_location_for_strategy = self._file_manager.get_strategy_save_location(strategy_num)
            file_locks_for_strategy = self._file_locks[strategy_num]

            exchange = Exchange(
                self._order_books_dict, self._order_books_dict_semaphore, self._subscription_queue, self._error_queue, strategy_num, self._stop_event, self._historical_api, save_data_location_for_strategy, file_locks_for_strategy)

            res = self._strategy_process_pool.apply_async(
                _run_strategy, args=(self._error_queue, strategy.strategy_func, exchange, *strategy.arguments))
            logger.debug(f"Started strategy {strategy_num}")

        logger.debug("Started strategies")
        self._error_processor._join_thread()
        logger.debug("Error processing thread joined")

        self._stop()

    def _stop(self, should_exit=True):
        logger.info("Stopping Program")
        self._stop_event.set()  # Inform child processes to stop

        # logger.info(self._error_processor.exception)
        # Prevents any other task from being submitted

        # close file manager before closing processes
        # if self._file_manager:
        #     self._file_manager.stop()

        if self._strategy_process_pool:  # Only close pool if it was opened
            logger.debug("Joining strategy processes")
            self._strategy_process_pool.close()
            self._strategy_process_pool.join()  # Wait for child processes to finish
            logger.debug("Processes strategy terminated")

        if self._graphing_process:
            logger.debug("Joining graph process")
            self._graphing_process.join()
            logger.debug("Graph process joined")

        if self._subscription_manager:
            self._subscription_manager.stop_queue_polling()
            logger.debug("Subscription manager stopped")

        # Clean up processes before the streamer as processes rely on streamer
        if self._custom_obj_manager:
            self._custom_obj_manager.shutdown()

        if self._streamer:
            self._streamer.stop()
            logger.debug("Streamer stopped")

        if self._error_processor:
            if self._error_processor.is_error:
                logger.error(f"PE: {self._error_processor.exception}")
            else:
                self._error_processor._stop_queue_polling()
            logger.debug("Error processor stopped")

        if should_exit:
            logger.info("Exiting")
            exit(0)  # All user work done so can exit
        logger.info("No exit in stop()")

    def _create_shared_memory(self, num_readers):
        self.manager = Manager()
        shared_dict = self.manager.dict()
        self._order_books_dict_semaphore = self.manager.Semaphore(num_readers)
        self._stop_event = self.manager.Event()

        return shared_dict

    def _exit_handler(self, signum, _):
        if signum == signal.SIGINT:
            logger.info("\nStopping...")
            if self._setup_finished:
                self._stop()
            else:
                self._pre_setup_terminate = True

    def register_strategy(self, strategy_func, *args):
        """Register a function to be executed. Include any arguments that the strategy function should be provided (any number of arguments is permissible). N.B. When the strategies are started, each strategy function
        is always provided with an :py:class:`Exchange <prototrade.exchange.exchange.Exchange>` object as the first parameter. This enables the strategy to interact with the framework.

        :param strategy_func: A strategy function to register
        :type strategy_func: function
        :param \*\ args: the parameters to pass to the strategy function, optional
        :type \*\ args: any
        """
        self.num_strategies += 1
        self._strategy_list.append(Strategy(strategy_func, args))

    def run_strategies(self):
        """
        Begins the execution of all strategies
        """
        try:
            self._create_components() # Try to start all the components and user strategies
        except Exception as e:
            self._stop(False)  # Cleanup then re-raise exception
            raise (e)

    def _create_components(self):
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

        self._start_custom_obj_manager()
        self._create_shared_api_class()

        self._subscription_queue = self.manager.Queue()

        self._subscription_manager = SubscriptionManager(self._streamer,
                                                         self._subscription_queue, SENTINEL)

        self._error_queue = self.manager.Queue()

        self._error_processor = ErrorProcessor(self._error_queue, SENTINEL)

        logger.debug("Creating streamer")

        self._setup_finished = True
        if self._pre_setup_terminate:
            self._stop()  # If CTRL-C pressed while setting up, then trigger stop now

        self._create_processes_for_strategies()

    def _register_custom_objects(self):
        _CustomManager.register(
            'HistoricalAPI', _HistoricalAPI, _HistoricalAPIProxy)
        _CustomManager.register(
            'FileManager', FileManager)
    
    def _start_custom_obj_manager(self):
        self._register_custom_objects()

        self._custom_obj_manager = _CustomManager()
        self._custom_obj_manager.start()

    # This creates a REST api object that is shareable across strategy processes. This means the user can query historical data
    def _create_shared_api_class(self):
        rest_api = self._custom_obj_manager.HistoricalAPI(
            self._streamer.get_rest_api())  # Pass in the actual rest api as a parameter
        # Get the api object within the class wrapper
        self._historical_api = rest_api.api

    def create_file_locks(self):
        for _ in range(self.num_strategies):
            self._file_locks.append(_StrategyLocks(self.manager.Lock(), self.manager.Lock())) #cannot be created inside FileManager as its a shared object


# This has to be outside the class, as otherwise all class members would have to be pickled when sending arguments to the new process
def _run_strategy(error_queue, func, exchange, *args):
    try:  # Wrap the user strategy in a try/catch block so we can catch any errors and forward them to the main process
        logger.info(f"Running {exchange.exchange_num}")
        func(exchange, *args)
    except Exception:
        try:       
            _handle_error(error_queue, exchange.exchange_num)
        except Exception as e2:
            logger.critical(
                f"During handling of a strategy error, another error occured: {e2}")
        finally:
            exchange._stop() # stop and cleanup main thread in exchange
        # At this point the process has finished and can be joined with the main process

def create_grapher(error_queue, *args):
    g = None
    try:  # Wrap the user strategy in a try/catch block so we can catch any errors and forward them to the main process
        g = _Grapher(*args)
        g.run_dash_app()
    except Exception:
        try:       
            _handle_error(error_queue, -1)
        except Exception as e2:
            logger.critical(
                f"During handling of a graphing error, another error occured: {e2}")
        finally:
            if g:
                g.stop() # stop grapher cleanly (e.g. remove locks)

def _handle_error(error_queue, exchange_num):
    logger.error(f"Process {exchange_num} EXCEPTION")
    # Get a string with full original stack trace
    exception_info = traceback.format_exc()
    error_queue.put(ErrorEvent(exchange_num, exception_info))

class _CustomManager(BaseManager):
    pass

class _HistoricalAPI:
    def __init__(self, api):
        self.api = api  # Holds the api to be used to acquire historical data

class _HistoricalAPIProxy(NamespaceProxy):
    # We need to expose the same __dunder__ methods as NamespaceProxy,
    # in addition to the b method.
    _exposed_ = ('__getattribute__', '__setattr__', '__delattr__', 'api')


class _FileManagerProxy(NamespaceProxy):
    # We need to expose the same __dunder__ methods as NamespaceProxy,
    # in addition to the b method.
    _exposed_ = ('__getattribute__', '__setattr__', '__delattr__', 'pnl_file_pointers', 'pos_file_pointers')

