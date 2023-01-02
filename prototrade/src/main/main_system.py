from multiprocessing import Process, Manager, Semaphore, Pool, current_process
from ticker_streamer.alpaca_streamer import AlpacaDataStreamer
from ticker_streamer.price_updater import PriceUpdater
from position_management.test_puller import TestPuller
import signal
import time

TEST_SYMBOLS = ["AAPL", "GOOG", "MSFT"]

class MainSystem:

    # this should be initialised with alpaca credentials and exchange. then register_strategy sued to calculate the num_strategiegs
    def __init__(self, num_strategies):
        self.num_strategies = num_strategies

        self.shared_order_books_dict = self._create_shared_memory(
            self.num_strategies)

        self.price_updater = PriceUpdater(
            self.shared_order_books_dict, self.sempahore_access, self.num_strategies)

        self.streamer = AlpacaDataStreamer(
            "AKFA6O7FWKEQ30SFPB9H",
            "z6Cb3RW4lyp3ykub09tUHjdGF7aNYsGuqXh7WWJs",
            self.price_updater,
            "iex"
        )

        self._create_position_managers()

    def _create_position_managers(self):
        # Temporarily ignore SIGINT to prevent interrupts being handled in child processes
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        self.tp_process_pool = Pool(self.num_strategies)

        # Set the handler for SIGINT. Now SIGINT is only handled in the main process
        signal.signal(signal.SIGINT, self._exit_handler)

        print("Creating readers")

        self.tp_list = []  # one per strategy
        for strategy_number in range(self.num_strategies):
            pm = TestPuller(
                self.shared_order_books_dict, self.sempahore_access, TEST_SYMBOLS, strategy_number, self.stop_event)
            self.tp_list.append(pm) # Add to list of position managers
            print(f"Created reader {strategy_number}")

    def stop_execution(self):
        print(f"Stopping {current_process().pid}")

        self.stop_event.set() #Inform child processes to stop
        self.streamer.stop()

        self.tp_process_pool.close() #Prevents any other task from being submitted
        self.tp_process_pool.join() #Wait for child processes to finish
        
        print("Processes terminated")
        exit(1)

    def _create_shared_memory(self, num_readers):
        manager = Manager()
        shared_dict = manager.dict()
        self.sempahore_access = manager.Semaphore(num_readers)
        self.stop_event = manager.Event()

        return shared_dict

    def _exit_handler(self, signum, _):
        if signum == signal.SIGINT:
            self.stop_execution()
    
    def test_execution(self):
        for symbol in TEST_SYMBOLS:
            self.streamer.subscribe(symbol)
        time.sleep(6)
        
        for pm in self.tp_list:  # start readers
            self.tp_process_pool.apply_async(pm.test_pull)
            print("Started test pull")
        print("Started readers")

        time.sleep(8)
        self.stop_execution()
