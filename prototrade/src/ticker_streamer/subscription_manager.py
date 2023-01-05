from collections import defaultdict
from models.subscription_event import SubscribeType
from threading import Thread

SENTINEL = None

class SubscriptionManager:

    def __init__(self, streamer, subscription_queue):
        self._streamer = streamer
        self._subscription_queue = subscription_queue

        self.symbol_to_strategies_dict = defaultdict(set)
        self._queue_polling_thread = None

        self._create_thread_to_poll_queue()

    def subscribe(self, strategy_num, symbol):
        if symbol not in self.symbol_to_strategies_dict:
            self._streamer.subscribe(symbol)

            self.symbol_to_strategies_dict[symbol].add(strategy_num)
            print(
                f"Strategy {strategy_num} subscribes to {symbol}")
        else:
            self.symbol_to_strategies_dict[symbol].add(strategy_num)
            print(
                f"Strategy {strategy_num} subscribes to {symbol}. Entry added")

    def unsubscribe(self, strategy_num, symbol):
        self.symbol_to_strategies_dict[symbol].remove(strategy_num)
        # if no strategies interested... unsubscribe permanantly
        if not self.symbol_to_strategies_dict[symbol]:
            self._streamer.unsubscribe(symbol)
            del self.symbol_to_strategies_dict[symbol]
            print(
                f"Strategy {strategy_num} unsubs from {symbol}. No strategies interested")

    def print_books_subscribed_to(self):
        print(*[key for key in self.symbol_to_strategies_dict], sep=",")

    def _create_thread_to_poll_queue(self):
        self._queue_polling_thread = Thread(
            target=self._process_subscription_events)
        self._queue_polling_thread.start()

    def _process_subscription_events(self):
        while True:
            event = self._subscription_queue.get()

            if event == SENTINEL:
                break

            if event.event_type == SubscribeType.SUBSCRIBE:
                self.subscribe(event.strategy_num, event.symbol)
            else:
                self.unsubscribe(event.strategy_num, event.symbol)

        print("Subscription queue reader finished")

    def stop_queue_polling(self):
        # self._subscription_queue.close()
        if self._queue_polling_thread:
            # Inform consumer thread to stop
            self._subscription_queue.put(SENTINEL)
            self._queue_polling_thread.join()
