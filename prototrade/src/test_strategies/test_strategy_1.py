from prototrade.prototrade import ProtoTrade
import time

def main():
    global pt
    pt = ProtoTrade()
    pt.register_strategy(test_strategy, 5, 8)
    pt.run_strategies()


def test_strategy(exchange, test_param_1, test_param_2):
    print(f"p1:{test_param_1} p2:{test_param_2}")

    exchange.subscribe("AAPL")
    exchange.subscribe("MSFT")
    while pt.is_running():
        order_books = exchange.get_subscribed_books()

        print("AAPL", order_books["AAPL"])
        print("-----------")

        time.sleep(0.5)


    print("Strategy Finished")

main()