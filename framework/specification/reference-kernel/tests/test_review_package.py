import json, tempfile, unittest
from pathlib import Path
from saef_kernel.review_package import validate_review_directory, DEFAULT_REQUIRED

class ReviewTests(unittest.TestCase):
    def make(self,root):
        for rel in DEFAULT_REQUIRED:
            p=Path(root)/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text('x')
        (Path(root)/'MANIFEST.json').write_text(json.dumps({'local_only':True,'clean_tree':True,'tests':[]}))
        # Do not checksum files in this minimal test.
        (Path(root)/'SHA256SUMS.txt').write_text('')
    def test_complete(self):
        with tempfile.TemporaryDirectory() as d:
            self.make(d); self.assertEqual(validate_review_directory(d),[])
    def test_missing(self):
        with tempfile.TemporaryDirectory() as d:
            self.make(d); (Path(d)/'git/head.txt').unlink(); self.assertTrue(any('git/head.txt' in x for x in validate_review_directory(d)))
    def test_dirty_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            self.make(d); (Path(d)/'MANIFEST.json').write_text(json.dumps({'local_only':True,'clean_tree':False,'tests':[]})); self.assertTrue(any('clean_tree' in x for x in validate_review_directory(d)))
    def test_failed_required_test(self):
        with tempfile.TemporaryDirectory() as d:
            self.make(d); (Path(d)/'MANIFEST.json').write_text(json.dumps({'local_only':True,'clean_tree':True,'tests':[{'id':'x','required':True,'exit_code':1}]})); self.assertTrue(any('required test failed' in x for x in validate_review_directory(d)))
