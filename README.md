# ProtoTrade

A Python library for the rapid prototyping of autotrading strategies


## Documentation

### Initialisation & Registering strategies

``` 
pt = ProtoTrade("alpaca", "API_USERNAME", "API_KEY", "sip") 

pt.register_strategy(test_strategy, 5, 8) # Name of function to call and parameters that function should take
pt.register_strategy(test_strategy_2, 6, 10, 11)  # Registering a second example function to run

pt.run_strategies() # Begins simulating execution of the two registered strategies
                    
```
                    
### Example Strategies

-- Insert mean reversion strategy --
