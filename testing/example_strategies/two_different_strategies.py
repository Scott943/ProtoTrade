from prototrade.strategy_registry import StrategyRegistry
from prototrade.enum import OrderType, OrderSide
import time
import random

def main():
    """
    We register two different strategies here.
    """
    pt = StrategyRegistry("alpaca",
                    "AKFA6O7FWKEQ30SFPB9H",
                    "z6Cb3RW4lyp3ykub09tUHjdGF7aNYsGuqXh7WWJs",
                    "sip")
    pt.register_strategy(test_strategy, lower_volume=1, upper_volume=3) # First variation of the strategy only places small volume orders
    pt.register_strategy(test_strategy_2) # Second variation of the strategy places higher volume orders
    pt.run_strategies()

def test_strategy(exchange, lower_volume, upper_volume):
    """
    Places a market order for AAPL every 3 seconds

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
        
        exchange.create_order("AAPL", OrderSide.BID, OrderType.MARKET, random.randrange(lower_volume, upper_volume)) # Example of placing an order with random volume within the limits

        for x in exchange.get_orders("AAPL").items():
            print(x)
        
        print("Transactions:", exchange.get_transactions())
        print("Positions", exchange.get_positions())

        print("---------------")
        time.sleep(3)


    print(f"Strategy {exchange.exchange_num} FINISHED")


def test_strategy_2(exchange):
    """
    Example arbitrary strategy that places orders for MSFT and AAPL.

    :param exchange: The exchange object that the strategy uses to interact with the framework
    :type exchange: :py:class:`Exchange <prototrade.exchange.exchange.Exchange>`
    :param lower_volume: The lower bound for the order's random volume 
    :type lower_volume: int
    :param upper_volume: The upper bound for the order's random volume
    :type upper_volume: int
    """

    exchange.subscribe("AAPL") # Subscribe to live data from Apple
    exchange.subscribe("MSFT")
    while exchange.is_running():
        quotes = exchange.get_subscribed_quotes()
        aapl_price = quotes["AAPL"]
        
        exchange.create_order("MSFT", OrderSide.BID if random.choice([True, False]) else OrderSide.ASK, OrderType.MARKET, random.randrange(5, 25)) # Example of placing an order with random volume within the limits

        prev_min_aapl_price = exchange.historical.get_latest_bar('AAPL').l
        current_aapl_holdings = exchange.get_positions()["AAPL"]
        if aapl_price.ask.price > prev_min_aapl_price and current_aapl_holdings > 50:
            # Creates an order that halves the AAPL holdings
            exchange.create_order("AAPL", OrderSide.ASK, OrderType.MARKET, round(current_aapl_holdings / 2))
        else:
            exchange.create_order("AAPL", OrderSide.BID, OrderType.MARKET, random.randrange(5, 12)) # Example of placing an order with random volume within the limits

        print("---------------")
        time.sleep(3)


    print(f"Strategy {exchange.exchange_num} FINISHED")
    

# Need this on Windows machines to avoid repeatedly spawning processes
if __name__ == '__main__': 
    main()