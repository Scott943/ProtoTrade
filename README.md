# ProtoTrade

A parallelised Python library for the rapid prototyping of autotrading strategies. Where other libraries typically backtest over historical data, this libary seamlessly hooks into live market data, and simulates the execution of user-defined strategies. The library supports the parallel execution of multiple strategies, allowing the user to easily compare their performance over the same market data:


<img src="https://user-images.githubusercontent.com/8079722/218773459-85885323-8d66-45cc-9a91-f1f6694aaa85.jpg" width="400">

## Documentation

Complete documentation and a quickstart guide can be found [here](https://scott943.github.io/Prototrade_Docs/quickstart.html).


### Example Strategy

The following code example defines a simple `test_strategy` that places a market order for Apple stock every 3 seconds.

```python
from prototrade.strategy_registry import StrategyRegistry
import time

def main():
    """Here we register a single strategy that repeatedly places a market order for Apple with a volume of 5."""
    pt = StrategyRegistry("alpaca", "[API_USERNAME]", "[API_KEY]", "sip")
    pt.register_strategy(test_strategy, 5) # Specify the volume to use here (as a contrived example)
    pt.run_strategies()

def test_strategy(exchange, vol_per_order):
    """Boilerplate strategy that retrieves the price of Apple stock and places a market order every 3 seconds

    exchange.subscribe("AAPL") # Subscribe to live data from Apple
    while exchange.is_running():
        quotes = exchange.get_subscribed_quotes()
        aapl_price = quotes["AAPL"]
        print(f"AAPL BID PRICE: {aapl_price.bid}")
        print(f"AAPL ASK PRICE: {aapl_price.ask}")
        
        exchange.create_order("AAPL", "bid", "market", vol_per_order) # Example of placing an order 
        time.sleep(3)
        
# Need this on Windows machines to avoid repeatedly spawning processes
if __name__ == '__main__': 
    main()
```
                    
See the [example strategies](https://scott943.github.io/Prototrade_Docs/example_strategies.html) page for further examples.
