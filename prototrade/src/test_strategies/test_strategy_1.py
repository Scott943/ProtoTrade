from prototrade.prototrade import ProtoTrade
import time
import random

def main():
    pt = ProtoTrade("alpaca",
                    "AKFA6O7FWKEQ30SFPB9H",
                    "z6Cb3RW4lyp3ykub09tUHjdGF7aNYsGuqXh7WWJs",
                    "iex")
    pt.register_strategy(test_strategy, 5, 8)
    # pt.register_strategy(test_strategy_2, 6, 10)
    pt.run_strategies()


def test_strategy(exchange, test_param_1, test_param_2):
    print(f"p1:{test_param_1} p2:{test_param_2}")

    exchange.subscribe("AAPL")
    while exchange.is_running():
        order_books = exchange.get_subscribed_books()
        aapl_price = order_books["AAPL"].bid.price
        print(f"AAPL BID PRICE: {aapl_price}")
        print(f"AAPL ASK PRICE: {order_books['AAPL'].ask.price}")
        print("FOK: ", exchange.create_order("AAPL", "ask", "fok", random.randrange(2,20), order_books['AAPL'].bid.price+random.choice([0,0.01])))

        for x in exchange.get_orders("AAPL").items():
            print(x)
        # print("BEST BID: ", exchange._position_manager._open_orders["AAPL"].ask_heap[0])
        time.sleep(1)

        symbol = "SPY"
        timeframe = "1Day"
        start = "2021-01-01"
        end = "2021-01-30"

        # Retrieve daily bars for SPY in a dataframe and printing the first 5 rows
        spy_bars = exchange.historical.get_bars(symbol, timeframe, start, end).df
        print(spy_bars)
        aapl_trades = exchange.historical.get_trades(symbol, limit=100).df
        print(aapl_trades)
        print("AAPL: position", exchange.get_positions("AAPL"))
        # print("Transactions:", exchange.get_transactions("AAPL"))
        # cancel_id = random.choice([k for k,_ in exchange.get_orders().items()])

        # exchange.cancel_order(cancel_id)
        # print(f"CANCELLED {cancel_id}")
        # for x in exchange.get_orders("AAPL").items():
        #     print(x)
        # time.sleep(5)
        
    print("Strategy 0 FINISHED")

def test_strategy_2(exchange, test_param_1, test_param_2):
    print(f"p1:{test_param_1} p2:{test_param_2}")
    
    exchange.subscribe("AAfPL")
    time.sleep(0.5)
    exchange.subscribe("GOOG")
    while exchange.is_running():
        order_books = exchange.get_subscribed_books()

        print("----------- S1")
        print(order_books)
        print()

        time.sleep(0.5)
    
    exchange.subscribe("MSFT") # This will correctly have no effect as queue is closed
    print("Strategy 1 FINISHED")


main()
