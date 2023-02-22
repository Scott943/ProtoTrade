from prototrade.strategy_registry import StrategyRegistry
from prototrade.enum import OrderType, OrderSide
import time
import pandas as pd
import matplotlib.pyplot as plt

def main():
    """Strategy that saves a png of the PnL every 3 seconds
    """
    pt = StrategyRegistry("alpaca",
                    "AKFA6O7FWKEQ30SFPB9H",
                    "z6Cb3RW4lyp3ykub09tUHjdGF7aNYsGuqXh7WWJs",
                    "sip",
                    "test_data")
    pt.register_strategy(test_strategy, vol_per_order=5) # Specify the volume to use here (as a contrived example)
    pt.run_strategies()


def test_strategy(exchange, vol_per_order):
    """
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

        pnl_over_time = exchange.get_pnl_over_time() # returns a list of lists.  
        # get_pnl_over_time() is a costly function so don't call this every loop in practice.

        plot_pnl(pnl_over_time) # user defined function to plot the pnl (see below)

        print("-----")
        time.sleep(3)
        
    print(f"Strategy {exchange.exchange_num} FINISHED")

def plot_pnl(pnl_over_time):
    if pnl_over_time:
        pnl_df = pd.DataFrame(pnl_over_time, columns = ['timestamp', 'pnl']) # convert to dataframe
        plt.plot(pnl_df['timestamp'], pnl_df['pnl'])
        plt.xlabel("TimeStamp")
        plt.ylabel("Profit / Loss")
        plt.gcf().autofmt_xdate()
        plt.savefig("pnl_for_strategy")

# Need this on Windows machines to avoid repeatedly spawning processes
if __name__ == '__main__': 
    main()