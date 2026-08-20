import unittest
from datetime import datetime, timezone
from saef_kernel.ids import stable_evidence_id, stable_claim_id, new_run_id

class IdTests(unittest.TestCase):
    def test_evidence_id_stable(self):
        self.assertEqual(stable_evidence_id('tool','x',{'b':2,'a':1}),stable_evidence_id('tool','x',{'a':1,'b':2}))
    def test_evidence_id_changes(self):
        self.assertNotEqual(stable_evidence_id('tool','x',1),stable_evidence_id('tool','x',2))
    def test_claim_whitespace_normalized(self):
        self.assertEqual(stable_claim_id('P01','inference','a  b'),stable_claim_id('P01','inference','a b'))
    def test_run_id_shape(self):
        value=new_run_id(datetime(2026,8,19,tzinfo=timezone.utc))
        self.assertTrue(value.startswith('RUN-20260819T000000Z-'))
