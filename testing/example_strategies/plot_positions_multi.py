from prototrade.strategy_registry import StrategyRegistry
from prototrade.enum import OrderType, OrderSide

import time
import pandas as pd
import matplotlib.pyplot as plt
import random
import matplotlib

def main():
    """We register a strategy that saves a .png of positions
    """
    print("Starting")
    pt = StrategyRegistry("alpaca",
                    "AKFA6O7FWKEQ30SFPB9H",
                    "z6Cb3RW4lyp3ykub09tUHjdGF7aNYsGuqXh7WWJs",
                    "sip",
                    "test_data")
    pt.register_strategy(test_strategy, 10, 30, 1, 50, 1, 10) # Specify the volume to use here (as a contrived example)
    pt.run_strategies()


def test_strategy(exchange, lower_vol_1, upper_vol_1, lower_vol_2, upper_vol_2, lower_vol_3, upper_vol_3):
    """Saves a .png every second of the number of PLTR, AAPL and MSFT positions that the strategy current holds

    :param exchange: The exchange object that the strategy uses to interact with the framework
    :type exchange: :py:class:`Exchange <prototrade.exchange.exchange.Exchange>`
    :param \*\ args: The volume parameters are used to specifiy the random.randrange arguments when placing market orders
    """
    exchange.subscribe("AAPL") # Subscribe to live data from Apple
    exchange.subscribe('PLTR')
    exchange.subscribe('MSFT')
    while exchange.is_running():
        quotes = exchange.get_subscribed_quotes()
        aapl_price = quotes["AAPL"]
        print(f"AAPL BID PRICE: {aapl_price.bid}")
        print(f"AAPL ASK PRICE: {aapl_price.ask}")
        
        exchange.create_order("AAPL", OrderSide.BID, OrderType.MARKET, random.randrange(lower_vol_1,upper_vol_1)) # Example of placing an order 
        time.sleep(0.5)
        exchange.create_order("PLTR", OrderSide.BID, OrderType.MARKET, random.randrange(lower_vol_2,upper_vol_2)) # Example of placing an order 
        exchange.create_order("MSFT", OrderSide.BID, OrderType.MARKET, random.randrange(lower_vol_3,upper_vol_3)) # Example of placing an order 
        time.sleep(1)
        exchange.create_order("AAPL", OrderSide.ASK, OrderType.MARKET, random.randrange(lower_vol_3,upper_vol_1)) # Example of placing an order 

        pos_over_time = exchange.get_positions_over_time() # retrieves position data on all stocks

        plot_positions(pos_over_time) # user defined function to plot the pnl (see below)

        print("--TEST--")
        time.sleep(1)
        
    print(f"Strategy {exchange.exchange_num} FINISHED")

def plot_positions(pos_over_time):
    if pos_over_time:
        pos_df = pd.DataFrame(pos_over_time, columns = ['timestamp', 'symbol', 'position']) # convert to dataframe
        fig,ax = plt.subplots()

        for symbol in pos_df['symbol'].unique():
            rows = pos_df[pos_df.symbol==symbol]
            ax.step(rows.timestamp, rows.position,label=symbol)
        
        ax.set_xlabel("TimeStamp")
        ax.set_ylabel("Position Amount")
        ax.legend(loc='best')
        plt.gcf().autofmt_xdate()
        fig.savefig("positions_for_strategy_multi")

# Need this on Windows machines to avoid repeatedly spawning processes
if __name__ == '__main__': 
    main()