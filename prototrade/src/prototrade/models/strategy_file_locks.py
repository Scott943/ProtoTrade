from multiprocessing import Lock

class _StrategyLocks:
   def __init__(self, pnl_lock, positions_lock):
      self.pnl_lock = pnl_lock
      self.positions_lock = positions_lock