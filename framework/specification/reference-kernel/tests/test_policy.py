import unittest
from saef_kernel.policy import ProductPolicy, Decision, evaluate_salesforce_shell

class PolicyTests(unittest.TestCase):
    def test_unknown_tool_denied(self):
        r=ProductPolicy({'get_deployment_result'}).evaluate_tool('delete_record')
        self.assertEqual(r.decision,Decision.DENY)
    def test_allowlisted_tool(self):
        r=ProductPolicy({'get_deployment_result'}).evaluate_tool('get_deployment_result')
        self.assertEqual(r.decision,Decision.ALLOW)
    def test_org_pin(self):
        p=ProductPolicy({'get_deployment_result'},allowed_orgs={'qa'})
        self.assertEqual(p.evaluate_tool('get_deployment_result','prod').decision,Decision.DENY)
        self.assertEqual(p.evaluate_tool('get_deployment_result','qa').decision,Decision.ALLOW)
    def test_deployment_report_allowed(self):
        r=evaluate_salesforce_shell('sf project deploy report --job-id 0AfX --target-org qa --json')
        self.assertEqual(r.decision,Decision.ALLOW)
    def test_most_recent_denied(self):
        r=evaluate_salesforce_shell('sf project deploy report --use-most-recent --json')
        self.assertEqual(r.decision,Decision.DENY)
    def test_deploy_start_denied(self):
        r=evaluate_salesforce_shell('sf project deploy start --source-dir force-app --json')
        self.assertEqual(r.decision,Decision.DENY)
    def test_compound_denied(self):
        for cmd in ['sf org display --json; sf project deploy start','sf org display --json && echo x','sf org display --json | cat','sf org display --json $(echo x)','sf org display --json > out']:
            with self.subTest(cmd=cmd): self.assertEqual(evaluate_salesforce_shell(cmd).decision,Decision.DENY)
    def test_wrapper_denied(self):
        self.assertEqual(evaluate_salesforce_shell("bash -c 'sf org display --json'").decision,Decision.DENY)
    def test_legacy_denied(self):
        self.assertEqual(evaluate_salesforce_shell('sfdx force:org:display --json').decision,Decision.DENY)
