import sys,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'scripts/qa'),str(R/'scripts/image')]
from check import scan_text
from bootimg import BootImage,read_cpio
class PrivacyAndBootTests(unittest.TestCase):
 def test_token_is_blocked_without_disclosing_value(self):
  value='gh'+'p_'+'A'*36
  findings=scan_text('value='+value)
  self.assertTrue(findings)
  self.assertNotIn(value,str(findings))
 def test_private_key_is_blocked(self):
  value='-----BEGIN '+'ENCRYPTED '+'PRIVATE KEY-----'
  self.assertTrue(scan_text(value))
 def test_password_assignment_is_blocked(self):
  self.assertTrue(scan_text('password='+'"'+'fictional-value'+'"'))
 def test_source_hash_is_allowed(self):
  self.assertEqual(scan_text('sha256='+'e9c7591b9a044f63d3fc4036cee778217ce7fe31a9a31c3cc5205b4977c9adce'),[])
 def test_truncated_boot_is_rejected(self):
  with self.assertRaises(ValueError):BootImage.parse(b'ANDROID!')
 def test_corrupt_cpio_is_rejected(self):
  with self.assertRaises(ValueError):read_cpio(b'070701'+b'0'*104)
if __name__=='__main__':unittest.main()
