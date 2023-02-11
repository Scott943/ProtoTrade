from multiprocessing import Lock

class _StrategyLocks:
   def __init__(self):
      self.pnl_lock = Lock()
      self.positions_lock = Lock()