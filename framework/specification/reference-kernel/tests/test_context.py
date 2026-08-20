import unittest
from saef_kernel.context import ContextBudget, ContextCandidate, compile_context_manifest, bound_tool_payload

class ContextTests(unittest.TestCase):
    def c(self,i,required=False,priority=0,relevance=0):
        return ContextCandidate(str(i),'knowledge',f'p/{i}',f'reason {i}','x'*40,priority,relevance,required)
    def test_target_selection(self):
        m=compile_context_manifest('RUN-X','stage',[self.c(i,priority=i) for i in range(20)],ContextBudget(8,12))
        self.assertEqual(m['totals']['files'],8); self.assertFalse(m['overflow'])
    def test_required_precedes_optional(self):
        m=compile_context_manifest('RUN-X','stage',[self.c(1,True),self.c(2,False,99)],ContextBudget(1,2))
        self.assertEqual(m['items'][0]['id'],'1')
    def test_required_overflow(self):
        m=compile_context_manifest('RUN-X','stage',[self.c(i,True) for i in range(13)],ContextBudget(8,12))
        self.assertTrue(m['overflow']); self.assertEqual(m['totals']['files'],12)
    def test_deduplicate(self):
        m=compile_context_manifest('RUN-X','stage',[self.c(1),self.c(1)],ContextBudget(8,12))
        self.assertEqual(m['candidate_count'],1)
    def test_deterministic(self):
        a=[self.c(i,priority=i%3,relevance=i/10) for i in range(12)]
        self.assertEqual(compile_context_manifest('R','s',a),compile_context_manifest('R','s',list(reversed(a))))
    def test_tool_payload_bound(self):
        data,truncated=bound_tool_payload('x'*40000,32768); self.assertTrue(truncated); self.assertEqual(len(data),32768)
    def test_invalid_budget(self):
        with self.assertRaises(ValueError): ContextBudget(12,8).validate()
