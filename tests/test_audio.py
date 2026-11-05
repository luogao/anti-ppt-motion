import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('audio',Path(__file__).resolve().parents[1]/'eval/import_audio.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class AudioTests(unittest.TestCase):
 def test_rejects_overlap(self):
  with self.assertRaises(ValueError):m.validate_clauses([{'start_s':0,'end_s':2,'text':'a'},{'start_s':1,'end_s':3,'text':'b'}],4)
 def test_rejects_out_of_range(self):
  with self.assertRaises(ValueError):m.validate_clauses([{'start_s':0,'end_s':5,'text':'a'}],4)
 def test_accepts_gaps_without_fabricating_words(self):
  m.validate_clauses([{'start_s':.1,'end_s':1,'text':'a'},{'start_s':2,'end_s':3,'text':'b'}],4)
if __name__=='__main__':unittest.main()
