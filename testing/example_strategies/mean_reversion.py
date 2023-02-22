from prototrade.strategy_registry import StrategyRegistry
from prototrade.models.enums import OrderSide, OrderType, MarketDataSource
import time
import datetime


POS_LIMIT = 20

def main():
    """Here we register several mean reversion strategies, each with different parameters
    """
    pt = StrategyRegistry(MarketDataSource.ALPACA,
                    "AKFA6O7FWKEQ30SFPB9H",
                    "z6Cb3RW4lyp3ykub09tUHjdGF7aNYsGuqXh7WWJs",
                    "sip",
                    "../test_data")

    # hyperparameter grid search
    starting_exp_factor = 0.95
    starting_divergence_percentage = 0.1
    for i in range(5):
      for j in range(4):
         exp_factor = starting_exp_factor + i * 0.011
         divergence_factor = starting_divergence_percentage + j * 0.1
         pt.register_strategy(mean_reversion_strategy, "AAPL", 5, exp_factor, divergence_factor, 5) 
    
    pt.run_strategies()


#14, 0.98, 0.11
def mean_reversion_strategy(exchange, ticker, vol_per_order, exp_factor, divergence_percentage, time_delay):
    """Mean reversion strategy. Buys if bid_price < EMA, sells if ask_price > EMA

    :param exchange: The exchange object that the strategy uses to interact with the framework
    :type exchange: :py:class:`Exchange <prototrade.exchange.exchange.Exchange>`
    :param vol_per_order: The volume to use for each order
    :type vol_per_order: int
    :param exp_factor: weights using older values verses newer values
    :type exp_factor: float
    :param divergence_percentage: the percent of bid price used in determining whether to place orders
    :type divergence_percentage: float
    :param time_delay: time between orders
    :type time_delay: float
    """
    exchange.subscribe(ticker) # Subscribe to live data from Apple
    
    # could make it so that we check if the exp. moving avg moves away from past 30 days avg

    average = (exchange.get_subscribed_quotes()[ticker].bid.price + exchange.get_subscribed_quotes()[ticker].ask.price)/2
    while exchange.is_running():
        quotes = exchange.get_subscribed_quotes()
        ticker_price = quotes[ticker]

        bid = ticker_price.bid.price
        ask = ticker_price.ask.price

        average = exp_factor * average + (1-exp_factor) * (bid+ask)/2

        divergence_amount = divergence_percentage/100 * (bid+ask)/2

        pos = exchange.get_positions()[ticker]
        if(average-bid > divergence_amount and pos < POS_LIMIT):
            exchange.create_order(ticker, OrderSide.BID, OrderType.MARKET, vol_per_order)
        if(ask-average > divergence_amount and pos > -POS_LIMIT):
            exchange.create_order(ticker, OrderSide.ASK, OrderType.MARKET, vol_per_order)
        
        time.sleep(time_delay)
        
    # Free to do any cleanup here (or data analytics for example)  
    print(f"Strategy {exchange.exchange_num} FINISHED")


# Need this on Windows machines to avoid repeatedly spawning processes
if __name__ == '__main__': 
    main()


def get_past_average(exchange,ticker):
    start_date = (datetime.datetime.now() - datetime.timedelta(30)).date()
    end_date = datetime.datetime.now().date()
    data = exchange.historical.get_bars(ticker, "1day", start_date, end_date).df
    return data["close"].mean()