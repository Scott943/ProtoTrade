# ProtoTrade

A parallelised Python library for the rapid prototyping of autotrading strategies. Where other libraries typically backtest over historical data, this libary seamlessly hooks into live market data, and simulates the execution of user-defined strategies. The library supports the parallel execution of multiple strategies, allowing the user to easily compare their performance over the same market data.

## Documentation

Complete documentation and a quickstart guide can be found [here](https://scott943.github.io/Prototrade_Docs/quickstart.html).
                    
### Installation

1. Ensure Python 3.8 or higher is installed (use `python3 --version` to check)
2. Use `pip install prototrade -U` to install the latest version of the package
3. Create a new python file (e.g. `script.py`) and paste in the [minimal boilerplate strategy](<https://scott943.github.io/Prototrade_Docs/_modules/example_strategies/minimal_boilerplate.html#main>).
4. Use `python3 script.py` to run the boilerplate code. 
