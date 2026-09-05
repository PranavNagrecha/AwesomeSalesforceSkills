# Connected App Troubleshooting — Triage Worksheet

Fill this at the start of a triage, before opening Setup. It captures the answers to
`SKILL.md` § Questions to Ask, so the runbook in `references/metadata-examples.md` § 1
can be walked with evidence instead of guesses. The machine-readable output of the same
triage is `templates/connected-app-diagnosis-record.yaml`.

## Scope

**Skill:** `connected-app-troubleshooting`

| Field | Value |
|---|---|
| Connected app label | |
| Org (production / sandbox name) | |
| Authenticating user Id (`005…`) | |
| Reported by / when | |
| Is this app still in production use? | |

## 1. The raw failure

Paste the response body verbatim. Replace consumer keys, secrets and tokens with `[REDACTED]`.
Do not paraphrase — the `error` string and the HTTP status are two different signals.

```text

```

| Field | Value |
|---|---|
| HTTP status | |
| Token-endpoint `error` value | |
| First observed failure (UTC) | |
| Last known success (UTC), if any | |

## 2. Which half of the dance

| Ask | Answer |
|---|---|
| Grant flow the client is using | |
| Initial authorization or renewal? (`LoginSubType` from § 2a) | |
| Did it ever work? | |
| Does it fail for all users or one? | |

If the answer to "did it ever work" is no, start at runbook rows 1–3.
If yes, start at rows 4–8.
If `LoginHistory` shows Success while the integration fails, go straight to row 11.

## 3. Evidence gathered

| Query | Run by | Holds Customize Application? | Rows returned | What it rules out |
|---|---|---|---|---|
| § 2a `LoginHistory` | | n/a | | |
| § 2b `OauthToken` | | | | |
| § 2c `SetupAuditTrail` | | n/a | | |

A zero-row result is a finding, not a blank. Record it.
An empty `OauthToken` result from a runner without Customize Application rules nothing out.

## 4. Policy fields inspected

Retrieved from the failing org, not read off the Setup screen.

| Field | Deployed value | Expected value | Matches? |
|---|---|---|---|
| `oauthConfig/isAdminApproved` | | | |
| `permissionSetName` / `profileName` | | | |
| `oauthConfig/callbackUrl` | | | |
| `oauthConfig/isSecretRequiredForRefreshToken` | | | |
| `oauthConfig/isConsumerSecretOptional` | | | |
| `oauthConfig/isRefreshTokenRotationEnabled` | | | |
| `oauthPolicy/refreshTokenPolicy` | | | |
| `oauthPolicy/ipRelaxation` | | | |

## 5. Diagnosis

| Field | Value |
|---|---|
| Runbook row matched | |
| `root-cause` category | |
| Causes explicitly ruled out, and by which evidence | |
| Confidence, and what would raise it | |

## 6. Fix and verification

| Field | Value |
|---|---|
| Change applied | |
| Reproduced in sandbox first? (yes / no / not applicable, with reason) | |
| Re-authorization performed? | |
| Verification query result (must include the previously failing `LoginSubType`) | |
| Follow-up owner, if the fix is a workaround | |

## 7. Checklist

- [ ] Error captured verbatim, secrets redacted.
- [ ] All three evidence queries run and results recorded, including zero-row results.
- [ ] `OauthToken` query run by someone holding Customize Application.
- [ ] `SetupAuditTrail` window starts before the first observed failure.
- [ ] Deployed policy read from a retrieve, not from Setup.
- [ ] Runbook row matched to evidence, not to the error string alone.
- [ ] Sandbox reproduction done, or its omission justified above.
- [ ] Verification shows Success on the grant type that was failing.
- [ ] `connected-app-diagnosis-record.yaml` filled and linted by the checker.

## 8. Notes

Record anything that did not fit a runbook row, and anything that would have shortened the
triage. A symptom the table cannot express is the strongest signal that the table needs a row.
