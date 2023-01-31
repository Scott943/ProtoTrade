import unittest
from pathlib import Path
import shutil
# import prototrade
# help(prototrade)
from prototrade.file_manager.file_manager import FileManager

class TestFileManager(unittest.TestCase):
   NUM_STRATEGIES = 4
   
   def setUp(self):
      self.file_manager = FileManager(Path(__file__).parent.resolve()/"sample_dir", self.NUM_STRATEGIES)
      p = Path(self.file_manager.root_path)

      rm_tree(p)

      for x in p.iterdir():
         print("x", x)

      (p/"Run_0").mkdir(parents=True, exist_ok=True)
      (p/"Run_5").mkdir(parents=True, exist_ok=True)

   # Test that the correct run index is generated
   def test_next_index_1(self):
      assert self.file_manager.get_run_index() == 6
   
   # Test that the required number of files are placed in the directory
   def test_strategy_dir(self):
      self.file_manager.create_directory_for_run()

      num_files = len(list(self.file_manager.strategy_path.iterdir()))

      assert num_files == self.NUM_STRATEGIES

      

def rm_tree(pth: Path):
    for child in pth.iterdir():
        if child.is_file():
            child.unlink()
        else:
            rm_tree(child)
    pth.rmdir()





if __name__ == '__main__':
    unittest.main()