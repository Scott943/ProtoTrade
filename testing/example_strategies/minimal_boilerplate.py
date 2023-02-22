from prototrade.strategy_registry import StrategyRegistry
from prototrade.models.enums import OrderType, OrderSide, MarketDataSource
import time

def main():
    """Here we register a single strategy that repeatedly places a market order for Apple with a volume of 5.
    """
    pt = StrategyRegistry(MarketDataSource.SIMULATED)
    pt.register_strategy(test_strategy, 5) # Specify the volume to use here (as a contrived example)
    pt.run_strategies()


def test_strategy(exchange, vol_per_order):
    """Boilerplate strategy that retrieves the price of Apple stock and places a market order every 3 seconds

    :param exchange: The exchange object that the strategy uses to interact with the framework (this parameter is provided by the StrategyRegistery)
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

        for x in exchange.get_orders("AAPL").items():
            print(x)
        print("Transactions:", exchange.get_transactions("AAPL"))
        print("Positions", exchange.get_positions())
        time.sleep(3)
        
    # Free to do any cleanup here (or data analytics for example)  
    print(f"Strategy {exchange.exchange_num} FINISHED")

# Need this on Windows machines to avoid repeatedly spawning processes
if __name__ == '__main__': 
    main()