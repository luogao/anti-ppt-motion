import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
spec=importlib.util.spec_from_file_location('review_page',Path(__file__).resolve().parents[1]/'eval/review_page.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class ReviewTests(unittest.TestCase):
 def test_group_reveal_is_not_shipped_in_review_page(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);batch=root/'batch';batch.mkdir()
   cases=[{'topic':'T1','repeat':1,'arm':a} for a in 'AB']
   (batch/'manifest.json').write_text(json.dumps({'results':cases}))
   html,key=m.build(batch,root/'review')
   self.assertEqual(len(key),2)
   self.assertNotIn('"arm"',html)
   self.assertNotIn('T1-r1-A',html)
   self.assertTrue((root/'review-reveal-key.json').is_file())
   self.assertNotIn('value="B"',html)
 def test_existing_reviews_are_not_overwritten(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'review';out.mkdir();(out/'index.html').write_text('existing')
   with self.assertRaises(FileExistsError):m.build(Path(d),out)

if __name__=='__main__':unittest.main()
