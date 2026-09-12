# M3-S02 test summary — Classic acknowledgement + escalation email templates

| Test | Type | Result | First line of failure output |
|---|---|---|---|
| xml | always-on | PASS (4/4 files parsed) | — |
| manifest | always-on | PASS (consistent) | — |
| `check_email_templates.py --manifest-dir artefacts/M3-S02 --strict` | checker | PASS (exit 0) | — |
| `check_email_deliverability_strategy.py --manifest-dir artefacts/M3-S02` | checker | PASS (exit 0, 3 WARNs — no assertion, see below) | — |
| `check-outputs` | precondition | PASS (`ok: true`, 0 missing/empty/malformed) | — |
| B06 (manual) | manual | deferred to M3 milestone gate | — |

## Detail

**xml** — parsed `artefacts/M3-S02/package.xml`, `email/case_intake.emailFolder-meta.xml`,
`email/case_intake/Case_Acknowledgement.email-meta.xml`,
`email/case_intake/Case_Escalated_To_Tier2.email-meta.xml`. All 4 well-formed. Raw capture:
`xml_results.json`.

**manifest** — two-way check against `artefacts/M3-S02/package.xml`:
- `EmailFolder` member `case_intake` <-> `email/case_intake.emailFolder-meta.xml` — present both ways.
- `EmailTemplate` member `case_intake/Case_Acknowledgement` <-> `.email` + `.email-meta.xml` pair — present both ways.
- `EmailTemplate` member `case_intake/Case_Escalated_To_Tier2` <-> `.email` + `.email-meta.xml` pair — present both ways.
- No wildcard members declared. `sender-identity-note.md` and `deploy-order.md` are documentation, not metadata, and are correctly outside the manifest per their own text ("They are not in package.xml and nothing deploys them.").
- Consistent in both directions.

**checker 1** (`check_email_templates.py --strict`) — stdout: `{"score": 100, "findings": [], "summary": "Scanned 4 email template file(s); 0 finding(s) detected."}`. Exit 0. Raw capture: `checker1_stdout.txt` / `checker1_stderr.txt`.

**checker 2** (`check_email_deliverability_strategy.py`) — stdout: `OK — no deliverability errors (3 warning(s)).` Exit 0. The 3 WARNs (no EmailAdministrationSettings/EmailAuthorizationSettings file, no deliverability-policy JSON, no DKIM-key-inventory JSON) are expected per the step's own acceptance-test description: this step declares none of those three files, so the checker asserts nothing about sender identity or deliverability posture here — that assertion is carried by the manual test (B06) and by sender-identity-note.md § 4, not by this exit code. Raw capture: `checker2_stdout.txt` / `checker2_stderr.txt`.

**check-outputs** — `{"ok": true, "step": "M3-S02", "missing": [], "empty": [], "malformed": []}`. All 7 declared outputs present, non-empty, and (where XML) parse. Raw capture: `check_outputs.json`.

**B06 (manual)** — Given/When/Then-shaped: Given support@ is both sender and Email-to-Case
routing address; When the note and both .email bodies are read; Then three named, observable
facts must hold. Checked against the artefacts on disk during this run for tickability (not for
pass/fail, which is the human's call at the gate):
- Both .email bodies (Case_Acknowledgement.email, Case_Escalated_To_Tier2.email) contain no
  email address at all — grepped, zero matches for `@`. Neither hardcodes a recipient or a
  reply-to.
- sender-identity-note.md § 1 names support@acme.example (both channels) and
  billing@acme.example (finance replies).
- sender-identity-note.md § 2 states the self-addressed-loop risk and names the control with
  both its qualifications (one-per-case does not bound a loop that grows by new cases;
  authorizedSenders empty makes the "rejects its own sender" half inert as configured).

All three observable outcomes are present on disk. The criterion names an observable outcome and
is therefore usable, not unusable — it is carried to skipped_manual[] for the human to tick at
the M3 gate, not ticked here.

## Process notes worth a human's attention (not failures)

sender-identity-note.md § 2 records an unresolved divergence between plan.json Q22
("support@ itself is the routing address") and answers-key.md's "Acknowledgement" row
("an org-wide email address, never the routing address itself"). No test in this step's
acceptance_tests[] asserts either reading — EmailTemplate has no sender element — so this
divergence does not fail anything here, but it is unresolved going into M3-S04, which is where
senderEmail actually gets set. Flagged in Process Observations in the run envelope.
