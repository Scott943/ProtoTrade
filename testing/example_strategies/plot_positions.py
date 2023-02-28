from prototrade.strategy_registry import StrategyRegistry
from prototrade.models.enums import OrderType, OrderSide, MarketDataSource
import time
import pandas as pd
import matplotlib.pyplot as plt
import random
import matplotlib

def main():
    """Register a strategy that saves a .png of the positions held by the strategy
    """
    print("Starting")
    pt = StrategyRegistry(MarketDataSource.ALPACA,
                    "AKFA6O7FWKEQ30SFPB9H",
                    "z6Cb3RW4lyp3ykub09tUHjdGF7aNYsGuqXh7WWJs",
                    "sip",
                    "test_data")
    pt.register_strategy(test_strategy) # Specify the volume to use here (as a contrived example)
    pt.run_strategies()


def test_strategy(exchange):
    """Register a strategy that saves a .png of the positions held by the strategy

    :param exchange: The exchange object that the strategy uses to interact with the framework
    :type exchange: :py:class:`Exchange <prototrade.exchange.exchange.Exchange>`
    """
    exchange.subscribe("AAPL") # Subscribe to live data from Apple
    while exchange.is_running():
        quotes = exchange.get_subscribed_quotes()
        aapl_price = quotes["AAPL"]
        print(f"AAPL BID PRICE: {aapl_price.bid}")
        print(f"AAPL ASK PRICE: {aapl_price.ask}")
        
        exchange.create_order("AAPL", OrderSide.BID, OrderType.MARKET, random.randrange(1,24)) # Example of placing an order 

        pos_over_time = exchange.get_positions_over_time("AAPL") # returns a list of lists.  
        # get_pnl_over_time() is a costly function so don't call this every loop in practice.

        plot_positions(pos_over_time) # user defined function to plot the pnl (see below)

        print("--TEST--")
        time.sleep(3)
        
    print(f"Strategy {exchange.exchange_num} FINISHED")

def plot_positions(pos_over_time):
    print(pos_over_time)
    if pos_over_time:
        pos_df = pd.DataFrame(pos_over_time, columns = ['timestamp', 'symbol', 'position']) # convert to dataframe
        plt.plot(pos_df['timestamp'], pos_df['position'])
        plt.xlabel("TimeStamp")
        plt.ylabel("AAPL Position Amount")
        plt.gcf().autofmt_xdate()
        plt.savefig("positions_for_strategy")

# Need this on Windows machines to avoid repeatedly spawning processes
if __name__ == '__main__': 
    main()