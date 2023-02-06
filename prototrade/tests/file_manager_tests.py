import unittest
from pathlib import Path
import shutil
# import prototrade
# help(prototrade)
from prototrade.file_manager.file_manager import FileManager

class TestFileManager(unittest.TestCase):
   
   
   def setUp(self):
      self.num_strategies = 4
      self.file_manager = FileManager(Path(__file__).parent.resolve()/"sample_dir", self.num_strategies)
      p = Path(self.file_manager.root_path)
      
      # Delete everything in sampel dir
      for x in p.iterdir():
         rm_tree(x)

      (p/"Run_0").mkdir(parents=True, exist_ok=True)
      (p/"Run_5").mkdir(parents=True, exist_ok=True)

   # Test that the correct run index is generated
   def test_next_index_1(self):
      assert self.file_manager.get_run_index() == 6
   
   # Test that the required number of files are placed in the directory
   def test_strategy_dir(self):
      self.file_manager.create_directory_for_run()

      num_files = len(list(self.file_manager.strategy_path.iterdir()))

      assert num_files == self.num_strategies

      

def rm_tree(pth: Path):
    for child in pth.iterdir():
        if child.is_file():
            child.unlink()
        else:
            rm_tree(child)
    pth.rmdir()





if __name__ == '__main__':
    unittest.main()