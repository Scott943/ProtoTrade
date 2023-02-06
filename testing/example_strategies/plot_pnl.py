from prototrade.strategy_registry import StrategyRegistry
import time
import pandas as pd
import matplotlib as plt

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
        
        exchange.create_order("AAPL", "bid", "market", vol_per_order) # Example of placing an order 

        pnl_over_time = exchange.get_pnl_over_time() # returns a list of lists
        pnl_pd = pd.DataFrame(pnl_over_time, columns = ['timestamp', 'pnl']) # convert to dataframe
        print(pnl_pd)

        if not pnl_pd.empty:
            plot = pnl_pd.plot(x="timestamp", y="pnl")
            plot.set_xlabel("TimeStamp")
            plot.set_ylabel("Profit / Loss")
            plt.savefig("pnl_for_strategy")

        print("-----")
        time.sleep(3)
        
    print("Strategy 0 FINISHED")

# Need this on Windows machines to avoid repeatedly spawning processes
if __name__ == '__main__': 
    main()