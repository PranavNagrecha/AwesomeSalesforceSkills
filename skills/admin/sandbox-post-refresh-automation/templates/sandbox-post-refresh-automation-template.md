# Sandbox Post Refresh Automation — Work Template

Fill this in during workflow step 1, before writing any Apex. Every row maps to a question in
`SKILL.md` § Questions to Ask Before Configuring.

**Skill:** `sandbox-post-refresh-automation`

**Request summary:**

---

## 1. Environment

| Field | Value |
|---|---|
| Source (production) org | |
| Target sandbox name (as `SandboxContext.sandboxName()` will report it) | |
| Tier (Developer / Developer Pro / Partial Copy / Full) | |
| Post-copy class name | |
| Already deployed to production? (yes / no / when) | |
| Bound to this sandbox? (Setup → Sandboxes → Apex Class) | |

---

## 2. Live job inventory

Paste the result of the six-state `CronTrigger` query from `references/metadata-examples.md` § 4.

| Job name | `JobType` | State | NextFireTime | Mutates external state? | Abort / keep |
|---|---|---|---|---|---|
| | | | | | |

Jobs kept alive, and who signed off:

---

## 3. Masking scope

| Field | Object | Auto-handled by the copy? | Masking rule |
|---|---|---|---|
| `Username` | User | Yes — sandbox-name suffix (api_meta L2711–2713) | none needed |
| `Email` | User | **No** | |
| | | | |

Active user count in the source org: ______  → sync loop or Queueable?

---

## 4. Step ownership

One row per step in `config/sandbox/post-refresh-checklist.json`.

| Step id | Owner (`apex` / `pipeline` / `manual`) | Idempotent? | Verify query or Setup check | Needs access the Automated Process user may lack? |
|---|---|---|---|---|
| `mask-user-email` | apex | | | |
| `deactivate-users` | apex | | | |
| `abort-scheduled-jobs` | apex | | | |
| `scrub-integration-config` | apex | | | |
| `reseed-reference-data` | | | | |
| `apply-environment-config` | | | | |
| `set-deliverability-access-level` | manual | | | |

Named owner for every `manual` row:

---

## 5. Failure and re-run

- Which steps are expected to fail under the Automated Process user's permissions?
- Post-activation re-run procedure (who, how, as which user):
- Where the run is logged:

---

## 6. Checklist

- [ ] Six-state `CronTrigger` inventory captured from the source org
- [ ] `config/sandbox/post-refresh-checklist.json` written, every step has `owner` + `verify`
- [ ] Class has a no-arg constructor and per-step try/catch
- [ ] Scrub ordered before abort
- [ ] Test uses the 5-arg `testSandboxPostCopyScript(..., true)`
- [ ] `python3 scripts/check_sandbox_post_refresh_automation.py --manifest-dir <dir>` passes
- [ ] Validated and deployed to production with `RunSpecifiedTests`
- [ ] Class bound to every sandbox that needs it
- [ ] Post-refresh verification queries run: 0 live jobs, 0 unmasked active users, `IsSandbox = true`
- [ ] `manual` rows worked and initialled

---

## 7. Notes

Deviations from the standard pattern, and why:
