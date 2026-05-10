"""Unit tests for the v0.4.3 credential redactor in sf_cli.py.

Triggered by a live session leak: ``sf org display`` prepended a warning
line, ``json.loads`` failed, and the error path returned raw stdout —
which contained the access token. These tests pin the redactor as a
regression guard.

All tokens in this file are MOCK strings. None are valid credentials.
The ``00DXXXXXXXXXX!`` and ``5AepXXX`` patterns mirror real Salesforce
token shape so the regex matchers exercise realistically.
"""

from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sfskills_mcp import sf_cli  # noqa: E402


# Mock token literals used throughout. None are real.
MOCK_SF_TOKEN = "00DVB0000ABCDEFGH!MockAccessTokenAAA111BBB222CCC333DDD444EEE555"
MOCK_REFRESH = "5AaPLACEHOLDER.test.fixture.NOT.real.aaabbbcccdddeeefff111"
MOCK_BEARER = "Bearer mock.jwt.header.payload.signature"


class RedactCredentialsTextTest(unittest.TestCase):
    def test_sf_session_token_redacted(self) -> None:
        text = f"accessToken={MOCK_SF_TOKEN} continues"
        out = sf_cli._redact_credentials_text(text)
        self.assertNotIn(MOCK_SF_TOKEN, out)
        self.assertIn("[REDACTED]", out)

    def test_oauth_refresh_redacted(self) -> None:
        text = f"refresh: {MOCK_REFRESH}"
        out = sf_cli._redact_credentials_text(text)
        self.assertNotIn(MOCK_REFRESH, out)
        self.assertIn("[REDACTED]", out)

    def test_bearer_redacted(self) -> None:
        text = f"Authorization: {MOCK_BEARER}"
        out = sf_cli._redact_credentials_text(text)
        self.assertNotIn("mock.jwt", out)
        self.assertIn("Bearer [REDACTED]", out)

    def test_non_credential_text_unchanged(self) -> None:
        # An org id is public-grade — should NOT be redacted alone.
        text = "Org id is 00DVB000007kvs52AA and the user is pn@example.com"
        out = sf_cli._redact_credentials_text(text)
        self.assertEqual(out, text)

    def test_empty_string(self) -> None:
        self.assertEqual(sf_cli._redact_credentials_text(""), "")

    def test_warning_prefix_plus_json_redacted(self) -> None:
        # Exact failure pattern from the live session that motivated this fix.
        text = (
            ' ›   Warning: @salesforce/cli update available\n'
            '{\n  "status": 0,\n  "result": {\n'
            f'    "accessToken": "{MOCK_SF_TOKEN}"\n'
            '  }\n}'
        )
        out = sf_cli._redact_credentials_text(text)
        self.assertNotIn(MOCK_SF_TOKEN, out)
        # Org id, alias, etc. that aren't tokens should survive.
        self.assertIn("Warning:", out)


class RedactCredentialsInPayloadTest(unittest.TestCase):
    def test_dict_accesstoken_redacted(self) -> None:
        payload = {"result": {"accessToken": MOCK_SF_TOKEN, "orgId": "00DVB000007kvs52AA"}}
        out = sf_cli._redact_credentials_in_payload(payload)
        self.assertEqual(out["result"]["accessToken"], "[REDACTED]")
        self.assertEqual(out["result"]["orgId"], "00DVB000007kvs52AA")

    def test_case_insensitive_key(self) -> None:
        # `AccessToken` in PascalCase, `accesstoken` lowercase — both redact.
        for key in ("accessToken", "AccessToken", "ACCESSTOKEN"):
            out = sf_cli._redact_credentials_in_payload({key: MOCK_SF_TOKEN})
            self.assertEqual(out[key], "[REDACTED]", f"key {key} not redacted")

    def test_nested_list_strings_redacted(self) -> None:
        payload = {"logs": [f"the token was {MOCK_SF_TOKEN} in line 42"]}
        out = sf_cli._redact_credentials_in_payload(payload)
        self.assertNotIn(MOCK_SF_TOKEN, str(out))

    def test_idempotent(self) -> None:
        payload = {"accessToken": MOCK_SF_TOKEN}
        once = sf_cli._redact_credentials_in_payload(payload)
        twice = sf_cli._redact_credentials_in_payload(once)
        self.assertEqual(once, twice)

    def test_preserves_non_dict_input(self) -> None:
        self.assertEqual(sf_cli._redact_credentials_in_payload(42), 42)
        self.assertEqual(sf_cli._redact_credentials_in_payload(True), True)
        self.assertIsNone(sf_cli._redact_credentials_in_payload(None))


class RunSfJsonRedactionIntegrationTest(unittest.TestCase):
    """Mock subprocess to prove run_sf_json never leaks a token, no matter
    which error path the call takes."""

    def _completed(self, returncode: int, stdout: str, stderr: str = "") -> mock.Mock:
        cp = mock.Mock()
        cp.returncode = returncode
        cp.stdout = stdout
        cp.stderr = stderr
        return cp

    def test_warning_prefix_breaks_json_no_token_in_error(self) -> None:
        # Reproduce the live-session leak: stdout has a warning line BEFORE JSON,
        # JSON parse fails, error path returns stdout. Token must not appear.
        leaky_stdout = (
            ' ›   Warning: update available\n'
            f'{{"result": {{"accessToken": "{MOCK_SF_TOKEN}"}}}}'
        )
        with mock.patch.object(sf_cli, "sf_binary", return_value="/fake/sf"), \
             mock.patch("subprocess.run", return_value=self._completed(0, leaky_stdout)):
            result = sf_cli.run_sf_json(["org", "display"])
        serialised = str(result)
        self.assertNotIn(MOCK_SF_TOKEN, serialised,
                         f"TOKEN LEAKED in error path: {serialised[:300]}")

    def test_successful_call_payload_token_redacted(self) -> None:
        good_json = f'{{"status": 0, "result": {{"accessToken": "{MOCK_SF_TOKEN}", "id": "00DVB000007kvs52AA"}}}}'
        with mock.patch.object(sf_cli, "sf_binary", return_value="/fake/sf"), \
             mock.patch("subprocess.run", return_value=self._completed(0, good_json)):
            result = sf_cli.run_sf_json(["org", "display"])
        self.assertNotIn(MOCK_SF_TOKEN, str(result))
        self.assertEqual(result["result"]["accessToken"], "[REDACTED]")
        # Public org id survives.
        self.assertEqual(result["result"]["id"], "00DVB000007kvs52AA")

    def test_nonzero_returncode_with_token_in_stderr(self) -> None:
        err_stderr = f"ERROR: session expired (token was {MOCK_SF_TOKEN})"
        with mock.patch.object(sf_cli, "sf_binary", return_value="/fake/sf"), \
             mock.patch("subprocess.run", return_value=self._completed(1, "{}", err_stderr)):
            result = sf_cli.run_sf_json(["org", "display"])
        self.assertNotIn(MOCK_SF_TOKEN, str(result))


class StripToJsonStartTest(unittest.TestCase):
    """v0.4.3 hardening: sf CLI prepends update-available / deprecation
    warning lines BEFORE JSON, breaking json.loads. ``_strip_to_json_start``
    skips to the first ``{`` or ``[``."""

    def test_warning_prefix_then_object(self) -> None:
        out = sf_cli._strip_to_json_start("Warning: foo\n{\"x\": 1}")
        self.assertEqual(out, '{"x": 1}')

    def test_warning_prefix_then_array(self) -> None:
        out = sf_cli._strip_to_json_start("›   Warning: bar\n[1,2,3]")
        self.assertEqual(out, "[1,2,3]")

    def test_already_clean_passes_through(self) -> None:
        self.assertEqual(sf_cli._strip_to_json_start('{"x": 1}'), '{"x": 1}')
        self.assertEqual(sf_cli._strip_to_json_start("[1,2]"), "[1,2]")

    def test_no_json_returns_empty(self) -> None:
        self.assertEqual(sf_cli._strip_to_json_start("no json here"), "")
        self.assertEqual(sf_cli._strip_to_json_start(""), "")

    def test_run_sf_json_handles_warning_prefix(self) -> None:
        """End-to-end: a mocked subprocess returning warning-prefixed JSON
        should parse cleanly. Pre-v0.4.3 this hit the JSONDecodeError path."""
        leaky_stdout = ' ›   Warning: update available\n{"status": 0, "result": {"id": "00D000000000000"}}'
        with mock.patch.object(sf_cli, "sf_binary", return_value="/fake/sf"), \
             mock.patch("subprocess.run", return_value=mock.Mock(
                 returncode=0, stdout=leaky_stdout, stderr=""
             )):
            result = sf_cli.run_sf_json(["org", "display"])
        # No error path; parsed JSON visible to caller.
        self.assertEqual(result.get("result", {}).get("id"), "00D000000000000")


class PerformanceTest(unittest.TestCase):
    def test_redactor_overhead_under_10ms_per_call(self) -> None:
        text = f"some random text without a token, repeated " * 50
        t0 = time.perf_counter()
        for _ in range(100):
            sf_cli._redact_credentials_text(text)
        elapsed_ms = (time.perf_counter() - t0) * 1000 / 100
        self.assertLess(elapsed_ms, 10.0, f"redactor too slow: {elapsed_ms:.2f}ms/call")


if __name__ == "__main__":
    unittest.main()
