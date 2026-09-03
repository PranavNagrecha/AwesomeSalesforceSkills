# LWC TypeScript Migration Plan

## Project Identity

- **Project root:**
- **Package directories:**
- **Source API version:**
- **Salesforce CLI version:**
- **Salesforce Extensions version:**
- **Target validation org / release:**
- **Observed date:**

## Toolchain Strategy

- **Strategy:** native TypeScript / local compile-to-JavaScript / defer
- **Evidence:** generated template, command help, official source, deploy validation
- **Canonical source:** `.ts` / `.js`
- **Generated output policy:** committed / ignored / CI-only
- **Rollback point:**

## Baseline Gates

| Gate | Command / evidence | Result |
|---|---|---|
| Type or JS check |  |  |
| Jest |  |  |
| Accessibility |  |  |
| Code Analyzer / ESLint |  |  |
| Deploy validation |  |  |
| Behavioral smoke |  |  |

## Bundle Inventory

| Bundle | Current language | Public API/events | Dependencies | Tests | Migration wave | Risk |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

## Configuration Changes

| File | Change | Why | Verification |
|---|---|---|---|
| `sfdx-project.json` |  |  |  |
| `package.json` |  |  |  |
| `tsconfig.json` |  |  |  |
| `.forceignore` / `.gitignore` |  |  |  |
| CI workflow |  |  |  |

## Per-Bundle Checklist

- [ ] Baseline behavior recorded
- [ ] Implementation renamed without changing `.js-meta.xml`
- [ ] Public properties/methods typed
- [ ] Event details and flags preserved
- [ ] Apex/wire/DOM boundaries typed and narrowed
- [ ] No blanket `any`, `@ts-ignore`, or double cast
- [ ] Type check and tests pass
- [ ] Static analysis passes
- [ ] Deploy validation passes
- [ ] Behavioral smoke matches baseline

## Risks and Rollback

| Risk | Detection | Mitigation | Rollback |
|---|---|---|---|
|  |  |  |  |

## Final Evidence

- **Clean-build hash / manifest:**
- **Deploy validation ID:**
- **Test result:**
- **Known limitations:**
