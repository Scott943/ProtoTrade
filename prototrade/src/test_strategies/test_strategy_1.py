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

    # exchange.subscribe("AAPL")
    while exchange.is_running():
        order_books = exchange.get_subscribed_books()

        exchange.create_order("AAPL", "ask", "limit", random.randrange(2,20), random.randrange(50,100))

        time.sleep(2)

        exchange.create_order("AAPL", "ask", "market", random.randrange(2,20))
        
        aapl_orders = exchange.get_orders("AAPL").items()
        for x in aapl_orders:
            print(x)
        print("BEST BID: ", exchange._position_manager._open_orders["AAPL"].ask_heap[0])
        time.sleep(2)

        cancel_id = random.choice([k for k,_ in exchange.get_orders().items()])
        

        exchange.cancel_order(cancel_id)
        print(f"CANCELLED {cancel_id}")
        for x in exchange.get_orders("AAPL").items():
            print(x)
        time.sleep(5)
        
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
