# Holds the function to execute and the required arguments

class Strategy:

    def __init__(self, strategy_func, args):
        self.strategy_func = strategy_func
        self.arguments = args