from prototrade.strategy_registry import StrategyRegistry
from prototrade.enum import OrderType, OrderSide
import time
import pandas as pd
import matplotlib.pyplot as plt

def main():
    """Here we register a single strategy that repeatedly places a market order for Apple with a volume of 5.
    """
    pt = StrategyRegistry("alpaca",
                    "AKFA6O7FWKEQ30SFPB9H",
                    "z6Cb3RW4lyp3ykub09tUHjdGF7aNYsGuqXh7WWJs",
                    "sip",
                    "test_data")
    pt.register_strategy(test_strategy, 5) # Specify the volume to use here (as a contrived example)
    pt.run_strategies()


def test_strategy(exchange, vol_per_order):
    """Boilerplate strategy that retrieves the price of Apple stock and places a market order every 3 seconds

    :param exchange: The exchange object that the strategy uses to interact with the framework
    :type exchange: :py:class:`Exchange <prototrade.exchange.exchange.Exchange>`
    :param vol_per_order: An example strategy argument where we specify the volume to use for each order
    :type vol_per_order: int
    """
    exchange.subscribe("AAPL") # Subscribe to live data from Apple
    while exchange.is_running():
        quotes = exchange.get_subscribed_quotes()
        aapl_price = quotes["AAPL"]
        print(f"AAPL BID PRICE: {aapl_price.bid}")
        print(f"AAPL ASK PRICE: {aapl_price.ask}")
        
        exchange.create_order("AAPL", OrderSide.BID, OrderType.MARKET, vol_per_order) # Example of placing an order 

        plot_aapl(exchange) # pass in the exchange to the user defined plotting function

        print("-----")
        time.sleep(3)
        
    print(f"Strategy {exchange.exchange_num} FINISHED")

def plot_aapl(exchange):
    aapl_price_bars = exchange.historical.get_bars("AAPL", "1minute", "2021-01-13", "2021-01-13").df
    # Reformat data (drop multiindex, rename columns, reset index)
    aapl_price_bars.columns = aapl_price_bars.columns.to_flat_index()
    aapl_price_bars.reset_index(inplace=True)

    # Plot stock price data
    plot = aapl_price_bars.plot(x="timestamp", y="close")
    plot.set_xlabel("Date")
    plot.set_ylabel("Apple Close Price ($)")
    plt.savefig("aapl_bars")


# Need this on Windows machines to avoid repeatedly spawning processes
if __name__ == '__main__': 
    main()