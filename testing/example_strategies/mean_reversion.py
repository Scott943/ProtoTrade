from prototrade.strategy_registry import StrategyRegistry
from prototrade.models.enums import OrderSide, OrderType, MarketDataSource
import time

POSITION_LIMIT = 20 # max no. shares owned at anyone one time
SYMBOL = "AAPL"
VOL_PER_ORDER = 5 # no. shares to buy between orders
TIME_DELAY = 5

INITIAL_ALPHA = 0.95 # weights the current EMA vs. new price
DIFF_ALPHA = 0.011

INITIAL_DIVERGENCE_MULTIPLIER = 0.001 # used to decide whether to buy/sell stock
DIFF_DIVERGENCE_MULTIPLIER = 0.001 # increments of 0.1%

def main():
    """Here we register several mean reversion strategies, each with different parameters, on the simulated exchange"""
    
    pt = StrategyRegistry(MarketDataSource.SIMULATED)
    
    # Hyperparameter grid search over strategy arguments
    for i in range(5):
        for j in range(4):
            alpha = INITIAL_ALPHA + (i*DIFF_ALPHA) # weights the current EMA vs. new price
            divergence_multiplier = INITIAL_DIVERGENCE_MULTIPLIER + (j*DIFF_DIVERGENCE_MULTIPLIER) # used to decide whether to buy/sell stock
            pt.register_strategy(mean_reversion_strategy, SYMBOL, alpha, divergence_multiplier) 
    
    pt.run_strategies()

def mean_reversion_strategy(exchange, symbol, alpha, divergence_multiplier):
    """Mean reversion strategy. Buys if bid < EMA, sells if ask > EMA

    :param exchange: The exchange object that the strategy uses to interact with the framework
    :type exchange: :py:class:`Exchange <prototrade.exchange.exchange.Exchange>`
    :param vol_per_order: The volume to use for each order
    :type vol_per_order: int
    :param alpha: weights using older values verses newer values
    :type alpha: float
    :param divergence_percentage: the percent of bid price used in determining whether to place orders
    :type divergence_percentage: float
    """
    exchange.subscribe(symbol) # subscribe to live data from the desired ticker symbol

    ticker_quote = exchange.get_subscribed_quotes()[symbol]
    average = (ticker_quote.bid.price + ticker_quote.ask.price)/2 # calculate initial average

    while exchange.is_running():
        ticker_quote = exchange.get_subscribed_quotes()[symbol]
        bid = ticker_quote.bid.price # highest price investors are willing to buy at
        ask = ticker_quote.ask.price # lowest price investors are willing to sell at

        average = alpha * average + (1-alpha) * (bid+ask)/2 # incorporate current price into moving average
        divergence_amount = divergence_multiplier * (bid+ask)/2

        positions_for_symbol = exchange.get_positions()[symbol] # get the number of shares that the strategy owns

        if(average-bid > divergence_amount and positions_for_symbol < POSITION_LIMIT): 
            exchange.create_order(symbol, OrderSide.BID, OrderType.MARKET, VOL_PER_ORDER) # insert buy order

        if(ask-average > divergence_amount and positions_for_symbol > -POSITION_LIMIT):
            exchange.create_order(symbol, OrderSide.ASK, OrderType.MARKET, VOL_PER_ORDER) # insert sell order
        
        time.sleep(TIME_DELAY)



# Need this on Windows machines to avoid repeatedly spawning processes
if __name__ == '__main__': 
    main()