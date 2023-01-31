from collections import defaultdict
from models.subscription_event import SubscribeType
from threading import Thread
import logging
from exceptions.exceptions import UnavailableSymbolException

class SubscriptionManager:

    def __init__(self, streamer, subscription_queue, SENTINEL):
        self._streamer = streamer
        self._subscription_queue = subscription_queue
        self._SENTINEL = SENTINEL

        self.symbol_to_strategies_dict = defaultdict(set)
        self._queue_polling_thread = None

        self._create_thread_to_poll_queue()

    def subscribe(self, strategy_num, symbol):
        if symbol not in self.symbol_to_strategies_dict:
            self._streamer.subscribe(symbol)

            self.symbol_to_strategies_dict[symbol].add(strategy_num)
            logging.info(
                f"Strategy {strategy_num + 1} subscribes to {symbol}")
        else:
            self.symbol_to_strategies_dict[symbol].add(strategy_num)
            logging.info(
                f"Strategy {strategy_num + 1} subscribes to {symbol}. Entry added")

    def unsubscribe(self, strategy_num, symbol):
        if symbol not in self.symbol_to_strategies_dict or strategy_num not in self.symbol_to_strategies_dict[symbol]:
            raise UnavailableSymbolException(f"Strategy {strategy_num + 1} attempted to unsubscribe from '{symbol}', which is not subscribed to")

        self.symbol_to_strategies_dict[symbol].remove(strategy_num)
        logging.info(f"Strategy {strategy_num + 1} unsubs from {symbol}.")
        # if no strategies interested... unsubscribe permanantly
        if not self.symbol_to_strategies_dict[symbol]: 
            self._streamer.unsubscribe(symbol)
            del self.symbol_to_strategies_dict[symbol] # remove the entry for the symbol (removes the set of strategies)
            logging.info(
                f"No strategies interested in {symbol}")

    def print_books_subscribed_to(self):
        logging.info(*[key for key in self.symbol_to_strategies_dict], sep=",")

    def _create_thread_to_poll_queue(self):
        self._queue_polling_thread = Thread(
            target=self._process_subscription_events)
        self._queue_polling_thread.start()

    def _process_subscription_events(self):
        while True:
            event = self._subscription_queue.get()

            if event == self._SENTINEL:
                break

            if event.event_type == SubscribeType.SUBSCRIBE:
                self.subscribe(event.strategy_num, event.symbol)
            else:
                self.unsubscribe(event.strategy_num, event.symbol)

        logging.info("Subscription queue reader finished")

    def stop_queue_polling(self):
        if self._queue_polling_thread:
            # Inform consumer thread to stop
            self._subscription_queue.put(self._SENTINEL)
            self._queue_polling_thread.join()
