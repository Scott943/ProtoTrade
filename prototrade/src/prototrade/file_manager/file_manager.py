from pathlib import Path
import regex
import csv

CHILD_DIR_PREFIX = "Run_"
DATETIME_FORMAT = "%y-%m-%d %H:%M:%S"

class FileManager:

   def __init__(self, root_path, num_strategies, file_locks):
      self.root_path = root_path
      self._num_strategies = num_strategies
      self._file_locks = file_locks
      self.run_number = self.get_run_index()
      self.create_directory_for_run()
      self.create_file_pointers()

   def create_directory_for_run(self):
      self.strategy_path = self.root_path/f"Run_{self.run_number}"
      self.strategy_path.mkdir(parents=True, exist_ok=False)

      for i in range(self._num_strategies):
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

   def create_file_pointers(self):
      self.pnl_file_pointers = []
      self.pos_file_pointers = []
      for strategy_num in range(self._num_strategies):
         loc = self.get_strategy_save_location(strategy_num)
         pnl_fp = open(loc/"PnL.csv", "a+")
         self.pnl_file_pointers.append(FileManagerObjects(pnl_fp, csv.writer(pnl_fp), csv.reader(pnl_fp)))

         pos_fp = open(loc/"Positions.csv", "a+")
         self.pos_file_pointers.append(FileManagerObjects(pos_fp, csv.writer(pnl_fp), csv.reader(pos_fp)))

   def stop(self):
      for obj in self.pnl_file_pointers:
         obj.fp.close()

      for obj in self.pos_file_pointers:
         obj.fp.close()

   def get_pnl_file_pointer(self, strategy):
      return 


class FileManagerObjects:
   def __init__(self, fp, csv_reader, csv_writer):
      self.fp = fp
      self.csv_reader = csv_reader
      self.csv_writer = csv_writer