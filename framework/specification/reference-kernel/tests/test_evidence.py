import unittest
from datetime import datetime, timezone
from saef_kernel.evidence import lint_claims, calculate_confidence

E={'id':'EV-AAAAAAAAAAAAAAAA','source_type':'salesforce','authority':5,'directness':5,'classification':'org-metadata','truncated':False,'fresh_until':'2099-01-01T00:00:00Z'}

class EvidenceTests(unittest.TestCase):
    def test_unsupported_material(self):
        f=lint_claims([{'id':'CL-X','type':'inference','material':True,'support':[]}],[])
        self.assertEqual(f[0]['code'],'unsupported_material_claim')
    def test_missing_ref(self):
        f=lint_claims([{'id':'CL-X','type':'inference','material':True,'support':[{'evidence_id':'EV-NO','relation':'supports'}]}],[E])
        self.assertTrue(any(x['code']=='missing_evidence_ref' for x in f))
    def test_contradiction(self):
        f=lint_claims([{'id':'CL-X','type':'inference','material':True,'status':'supported','support':[{'evidence_id':E['id'],'relation':'contradicts'}]}],[E])
        self.assertTrue(any(x['code']=='supported_despite_contradiction' for x in f))
    def test_secret_evidence(self):
        sec=dict(E,classification='credential-secret')
        f=lint_claims([{'id':'CL-X','type':'inference','material':True,'support':[{'evidence_id':E['id'],'relation':'supports'}]}],[sec])
        self.assertTrue(any(x['code']=='secret_evidence_exposed' for x in f))
    def test_high_confidence(self):
        c={'support':[{'evidence_id':E['id'],'relation':'supports'}]}
        result=calculate_confidence(c,{E['id']:E},datetime(2026,8,19,tzinfo=timezone.utc))
        self.assertEqual(result['label'],'high')
    def test_contradiction_penalty(self):
        c={'support':[{'evidence_id':E['id'],'relation':'contradicts'}]}
        result=calculate_confidence(c,{E['id']:E})
        self.assertNotEqual(result['label'],'high')
