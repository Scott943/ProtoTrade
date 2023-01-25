
class UnavailableSymbolException(Exception):
    pass


class SubscriptionException(Exception):
    pass

class InvalidOrderTypeException(Exception):
    pass

class InvalidOrderSideException(Exception):
    pass

class UnknownOrderIdException(Exception):
    pass

class MissingParameterException(Exception):
    pass

class ExtraneousParameterException(Exception):
    pass

class InvalidPriceException(Exception):
    pass

class InvalidVolumeException(Exception):
    pass

class ExchangeNotOpenException(Exception):
    pass