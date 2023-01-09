from prototrade.prototrade import ProtoTrade
import time


def main():
    pt = ProtoTrade("alpaca",
                    "AKFA6O7FWKEQ30SFPB9H",
                    "z6Cb3RW4lyp3ykub09tUHjdGF7aNYsGuqXh7WWJs",
                    "iex")
    pt.register_strategy(test_strategy, 5, 8)
    pt.register_strategy(test_strategy_2, 6, 10)
    pt.run_strategies()


def test_strategy(exchange, test_param_1, test_param_2):
    print(f"p1:{test_param_1} p2:{test_param_2}")

    exchange.subscribe("AAPL")
    while exchange.is_running():
        order_books = exchange.get_subscribed_books()

        print("----------- S0")
        print(order_books)
        print()
        
        
        time.sleep(0.5)
    
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
