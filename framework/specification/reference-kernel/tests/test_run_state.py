import unittest
from saef_kernel.run_state import RunStateMachine, InvalidTransition

class RunStateTests(unittest.TestCase):
    def test_happy_path(self):
        r=RunStateMachine('RUN-X')
        for s in ['preflighted','input_validated','planned','context_ready','evidence_gathering','evidence_ready','diagnosing','draft_ready','reviewing','completed']:
            r.transition(s,'test','ok')
        self.assertTrue(r.terminal); self.assertEqual(len(r.history),10)
    def test_invalid_skip(self):
        with self.assertRaises(InvalidTransition): RunStateMachine('R').transition('completed','x','x')
    def test_terminal_immutable(self):
        r=RunStateMachine('R'); r.transition('refused','x','unsafe')
        with self.assertRaises(InvalidTransition): r.transition('planned','x','no')
    def test_checkpoint_resume(self):
        r=RunStateMachine('R'); r.transition('preflighted','x','x'); r.transition('input_validated','x','x'); r.transition('planned','x','x'); r.transition('checkpointed','x','compact'); r.transition('context_ready','x','resume')
        self.assertEqual(r.state,'context_ready')
