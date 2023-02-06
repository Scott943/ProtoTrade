from pathlib import Path
import regex

CHILD_DIR_PREFIX = "Run_"

class FileManager:

   def __init__(self, root_path, num_strategies):
      self.root_path = root_path
      self.num_strategies = num_strategies
      self.run_number = self.get_run_index()
      self.create_directory_for_run()

   def create_directory_for_run(self):
      self.strategy_path = self.root_path/f"Run_{self.run_number}"
      self.strategy_path.mkdir(parents=True, exist_ok=False)

      for i in range(self.num_strategies):
         (self.strategy_path/f"Strategy_{i}").mkdir(parents=True, exist_ok=False)
         (self.strategy_path/f"Strategy_{i}/Transactions.csv").touch()
         (self.strategy_path/f"Strategy_{i}/PnL.csv").touch()
      

   def get_run_index(self):
      max_run_dir = -1
      for dir_child in Path.iterdir(self.root_path):
         if Path.is_dir and CHILD_DIR_PREFIX in dir_child.name:
            split_arr = dir_child.name.split(CHILD_DIR_PREFIX)
            if len(split_arr) >= 2 and split_arr[1].isnumeric():
               max_run_dir = max(max_run_dir, int(split_arr[1]))
      
      return max_run_dir + 1

   def get_strategy_save_location(self, strategy_number):
      return self.root_path/f"Run_{self.run_number}"/f"Strategy_{strategy_number}"
