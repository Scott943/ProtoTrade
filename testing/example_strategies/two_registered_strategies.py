from prototrade.strategy_registry import StrategyRegistry
import time
import random
from matplotlib import pyplot as plt
import pandas as pd

def main():
    """
    We register two strategies here (both executing the same function but with different function parameters). 
    One strategy repeatedly places orders of low volume, whilst the other places orders with a higher volume.
    """
    pt = StrategyRegistry("alpaca",
                    "AKFA6O7FWKEQ30SFPB9H",
                    "z6Cb3RW4lyp3ykub09tUHjdGF7aNYsGuqXh7WWJs",
                    "sip")
    pt.register_strategy(test_strategy, 1, 3) # First variation of the strategy only places small volume orders
    pt.register_strategy(test_strategy, 10, 20) # Second variation of the strategy places higher volume orders
    pt.run_strategies()


def test_strategy(exchange, lower_volume, upper_volume):
    """
    Boilerplate strategy that retrieves the price of Apple stock and places a market order every 3 seconds.
    Takes in two arguments, lower_volume and upper_volume. These illustrate how we can pass
    in different parameters to alter the execution of the strategy.

    :param exchange: The exchange object that the strategy uses to interact with the framework
    :type exchange: :py:class:`Exchange <prototrade.exchange.exchange.Exchange>`
    :param lower_volume: The lower bound for the order's random volume 
    :type lower_volume: int
    :param upper_volume: The upper bound for the order's random volume
    :type upper_volume: int
    """

    print(f"Lower volume:{lower_volume} p2:{upper_volume}")

    exchange.subscribe("AAPL") # Subscribe to live data from Apple
    while exchange.is_running():
        quotes = exchange.get_subscribed_quotes()
        aapl_price = quotes["AAPL"]
        print(f"AAPL BID PRICE: {aapl_price.bid}")
        print(f"AAPL ASK PRICE: {aapl_price.ask}")
        
        exchange.create_order("AAPL", "bid", "market", random.randrange(lower_volume, upper_volume)) # Example of placing an order with random volume within the limits

        for x in exchange.get_orders("AAPL").items():
            print(x)
        
        print("Transactions:", exchange.get_transactions())
        print("Positions", exchange.get_positions())

        print("---------------")
        time.sleep(3)


    print("Strategy 0 FINISHED")
    

# Need this on Windows machines to avoid repeatedly spawning processes
if __name__ == '__main__': 
    main()