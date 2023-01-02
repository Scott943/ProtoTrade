from multiprocessing import Process, Manager, Semaphore, Pool
from ticker_streamer.ticker_streamer import AlpacaDataStreamer
from ticker_streamer.price_updater import PriceUpdater
from models.positions_manager import PositionsManager
import signal
import time

TEST_SYMBOLS = ["AAPL", "GOOG", "MSFT"]


class MainSystem:

    def __init__(self, num_strategies):
        signal.signal(signal.SIGINT, self.exit_handler)

        self.num_strategies = num_strategies
        self.is_stopping = False

        self.shared_order_books_dict = self.create_shared_memory(
            num_strategies)

        self.price_updater = PriceUpdater(
            self.shared_order_books_dict, sempahore_access, num_strategies)

        self.streamer = AlpacaDataStreamer(
            "AKFA6O7FWKEQ30SFPB9H",
            "z6Cb3RW4lyp3ykub09tUHjdGF7aNYsGuqXh7WWJs",
            self.price_updater,
            "iex"
        )

        self.positions_managers_process_pool = Pool(num_strategies)
        self.positions_managers = []  # one per strategy

        print("Creating readers")
        for i in range(self.num_user_strategies):
            pm = PositionsManager(
                self.shared_order_books_dict, sempahore_access, TEST_SYMBOLS, i)
            self.positions_managers.append(pm)
            print(f"Created reader {i}")

        print("Connection established")

    def stop_execution(self):
        if self.is_stopping:
            return

        self.is_stopping = True
        self.streamer.stop()
        self.positions_managers_process_pool.terminate()
        print("Processes terminated")
        exit(1)

    def create_shared_memory(self, num_readers):
        global sempahore_access

        manager = Manager()
        shared_dict = manager.dict()
        sempahore_access = manager.Semaphore(num_readers)

        return shared_dict

    def exit_handler(self, signum, _):
        if signum == signal.SIGINT:
            self.stop_execution()

    def test_execution(self):
        for symbol in TEST_SYMBOLS:
            self.streamer.subscribe(symbol)
        time.sleep(6)

        for pm in self.positions_managers:  # start readers
            self.positions_managers_process_pool.apply_async(pm.test_pull)
        print("Started readers")

        time.sleep(8)
        self.stop_execution()
