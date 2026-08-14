# RESUME — 2026-08-14 session 2 (finish in-flight work)

**HEAD still:** `c536d3911` on `overhaul/2026-08-01-checkpoint`.
**Do not commit** unless the user asks. Working tree is large and uncommitted.

## Done this session

- **19 benchmark relabels** applied to `evals/measurement/heldout-queries.json`.
- **Model-routing harness** landed:
  - `evals/measurement/run_model_routing.py`
  - `evals/measurement/README-model-routing.md`
  - README-heldout.md now lists four harnesses
  - Raw saved run: Hit@1 **79.2%** / Hit@3 **91.6%**
  - Re-scored with relabels: Hit@1 **90.9%** / Hit@3 **96.8%**
- **22 routing-fix chunks** applied (router `DOMAIN_META` in `scripts/build_plugin.py` + skill descriptions / triggers). Plugin regenerated; descriptions kept under the 900-char cap.
- **Blocked packages:** stubs/wf already at skill_doctor ready except `devops/salesforce-code-analyzer` placeholder (`TODO` in a regex example) — **fixed**.
- **Currency remaining 4 groups:**
  - `lwc/lwc-local-development` — corrected (auto-install plugin, stripped unverified April 13 GA, removed invented `--client-select`, `--ssr` Spring '26).
  - `agentforce/agentforce-grid` — Flex Credits vs $2/conversation note added (help.salesforce.com rates not inlined).
  - `data/data-cloud-code-extensions` — already current on HEAD; no edit.
  - `admin/acceptance-criteria-given-when-then` — **REFUSED** Named Query API fact (wrong package).
  - `apex/einstein-activity-capture-api` — **CLEAN** (Spring '27 already absorbed).
- Fixture leftover from deleted trigger retargeted:
  `custom event not reaching parent use lms or api` →
  `three components need to coordinate and I do not know whether to use @api, events, or LMS`

## Still mid-flight (subagents)

Two agents were launched to:
1. Fix remaining **dead `use domain/slug` redirects** in descriptions
2. Spot-check the 16 routing chunks that were edited but never adversarially reviewed

Reconcile their diffs before treating routing-r1/r2 as shipped.

## Next commands (no commit)

```bash
python3 scripts/skill_sync.py --all --skip-embeddings
python3 scripts/build_plugin.py
python3 scripts/validate_repo.py --skills-only
python3 evals/measurement/run_model_routing.py --check
```

Rebuild embeddings only if you need held-out FTS numbers; they do not ship.

## Standing rules (do not re-break)

- Apex trigger access: sharing declaration fixed `without sharing`; DB ops default **user mode** at API 67.0+.
- `help.salesforce.com` crawler-blocked → UNVERIFIABLE unless already absorbed from a verified fetch.
- Adversarial review before shipping enrichment waves (~1 fabrication / 3 packages).
