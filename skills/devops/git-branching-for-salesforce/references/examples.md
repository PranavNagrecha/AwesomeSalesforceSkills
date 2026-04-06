# Examples — Git Branching For Salesforce

## Example 1: Trunk-Based Strategy for a 6-Person Team

**Context:** A team of 6 developers works on a single Salesforce org using SFDX with scratch orgs. They release to production every two weeks. They have one Developer Pro sandbox for integration testing and one Partial Copy sandbox for UAT.

**Problem:** Without a defined branching model, developers push directly to `main`, breaking CI for others. Metadata conflicts pile up because multiple developers edit the same profiles.

**Solution:**

```text
Branch Model:
  main ─────────────────────────────────────────────► (production)
    │                                                    │
    ├── feature/W-1234-account-validation ──► PR ──► merge
    │     └── scratch org (developer's own)
    │
    ├── feature/W-1235-opportunity-trigger ──► PR ──► merge
    │     └── scratch org (developer's own)
    │
    └── (tag: v2024.03.15 after deploy to prod)

Org Mapping:
  main           → Integration sandbox (auto-deploy on merge)
  release tag    → UAT sandbox (manual deploy for sign-off)
  production tag → Production (deploy after UAT approval)
```

Branch protection on `main`:
- Require 1 PR review
- Require passing CI: `sf project deploy validate --target-org integration`
- No direct pushes

**Why it works:** Short-lived feature branches (1-3 days) minimize merge conflicts. Each developer works in an isolated scratch org, so there is no contention on shared environments during development. The integration sandbox catches cross-feature issues before UAT.

---

## Example 2: Environment Branching for a 20-Person Program

**Context:** A large enterprise program with 20 developers across 3 workstreams, compliance-gated releases, and a 6-week release cycle. They have Full Copy, Partial Copy, and multiple Developer sandboxes.

**Problem:** Features from different workstreams need independent UAT cycles. A single `main` branch cannot isolate release candidates when workstreams move at different speeds.

**Solution:**

```text
Branch Model:
  main (production mirror) ──────────────────────────────────────►
    │                             ▲                    ▲
    │                             │ merge after deploy │ hotfix merge
    │                             │                    │
    ├── develop ──────────────────┤                    │
    │     │        ▲    ▲    ▲    │                    │
    │     │        │    │    │    │                    │
    │     ├── feature/WS1-*  │    │                    │
    │     ├── feature/WS2-*  │    │                    │
    │     └── feature/WS3-*  │    │                    │
    │                             │                    │
    ├── release/2024.Q2 ─────────┘                    │
    │     └── UAT sandbox                              │
    │                                                  │
    └── hotfix/PROD-4567 ─────────────────────────────┘
          └── Full Copy sandbox (prod data for repro)

Org Mapping:
  develop        → Developer Pro sandbox (continuous integration)
  release/*      → Partial Copy sandbox (UAT)
  main           → Production
  hotfix/*       → Full Copy sandbox (production replica)
```

**Why it works:** The `release/*` branch freezes the scope for UAT while `develop` continues accepting new features for the next cycle. Hotfixes bypass the normal flow and merge into both `main` and `develop` to prevent regression.

---

## Example 3: Package-Aligned Branching for Unlocked Packages

**Context:** A team maintains 4 unlocked packages: `core-model`, `sales-automation`, `service-extensions`, and `analytics-dashboards`. Each package releases independently. The team uses trunk-based development as the base model.

**Problem:** Creating package versions from feature branches produces orphan versions that cannot be promoted because they break the linear ancestry chain.

**Solution:**

```text
Branch Model:
  main ─────────────────────────────────────────────────►
    │                                    ▲
    ├── feature/core-model/W-100 ──► PR ─┤
    ├── feature/sales-auto/W-101 ──► PR ─┤
    │                                    │
    └── (CI on main creates package versions)

sfdx-project.json on main:
  "packageDirectories": [
    { "package": "core-model",        "versionNumber": "1.3.0.NEXT", "ancestorVersion": "1.2.0.1" },
    { "package": "sales-automation",  "versionNumber": "2.1.0.NEXT", "ancestorVersion": "2.0.0.5" },
    ...
  ]

CI pipeline (on merge to main):
  1. Detect which package directories changed
  2. Run: sf package version create -p <changed-package> --wait 20
  3. Install in integration scratch org
  4. Run Apex tests
  5. On release: sf package version promote -p <package-version-id>
  6. Tag main with package version
```

**Why it works:** Package versions are only created from `main`, preserving the linear ancestry chain. Feature branches develop and test in scratch orgs without creating package versions. The CI pipeline detects which packages changed and only versions those.

---

## Anti-Pattern: Long-Lived Feature Branches with Shared Sandboxes

**What practitioners do:** Create a feature branch per workstream that lives for 4-8 weeks. Each feature branch maps to a shared Developer sandbox where 3-4 developers push changes. Merges to `develop` happen only at the end of the sprint.

**What goes wrong:** The shared sandbox drifts from the branch because developers make declarative changes (fields, layouts, flows) directly in the org without pulling to source. When the branch finally merges, massive conflicts arise in profiles, permission sets, and custom labels. Resolving these conflicts takes days and often introduces regressions.

**Correct approach:** Keep feature branches short-lived (< 5 days). Each developer uses their own scratch org. Pull and commit declarative changes daily using `sf project retrieve start`. Merge to the integration branch frequently. If workstream isolation is required, use environment branching with a proper integration step, not long-lived feature branches with shared sandboxes.
