from prototrade.virtual_exchange import VirtualExchange
import time

def main():
    pt = VirtualExchange("alpaca",
                    "AKFA6O7FWKEQ30SFPB9H",
                    "z6Cb3RW4lyp3ykub09tUHjdGF7aNYsGuqXh7WWJs",
                    "sip")
    pt.register_strategy(test_strategy, 5)
    pt.run_strategies()

# Boilerplate strategy that retrieves the price of Apple stock and places a market order every 3 seconds
# Example parameters to to specify the arguments for the random.randrange function in the market order
def test_strategy(exchange, vol_per_order):
    exchange.subscribe("AAPL") # Subscribe to live data from Apple
    while exchange.is_running():
        order_books = exchange.get_subscribed_books()
        aapl_price = order_books["AAPL"]
        print(f"AAPL BID PRICE: {aapl_price.bid}")
        print(f"AAPL ASK PRICE: {aapl_price.ask}")
        
        exchange.create_order("AAPL", "bid", "market", vol_per_order) # Example of placing an order with random volume within the limits

        for x in exchange.get_orders("AAPL").items():
            print(x)
        
        print("Transactions:", exchange.get_transactions())
        print("Positions", exchange.get_positions())
        time.sleep(3)
        
    print("Strategy 0 FINISHED")

# Need this on Windows machines to avoid repeatedly spawning processes
if __name__ == '__main__': 
    main()