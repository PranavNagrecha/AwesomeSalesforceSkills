# Examples — LWC Performance Budgets

A budget is only a budget if something fails when it is exceeded. The examples
below build one that can fail, and pick metrics that are actually measurable in
a Salesforce context — which rules out several that look obvious.

---

## What you can and cannot measure

This is the section that determines whether a budget manifest is real or
aspirational.

| Metric | Measurable? | How |
|---|---|---|
| Source bytes per LWC bundle | Yes | `wc -c` over the bundle, in CI, before deploy |
| Transitive import weight | Yes | Static import graph over `force-app/.../lwc` |
| `@wire` count per component | Yes | Static count |
| Imperative Apex calls per user action | Yes | Static count + a DevTools network trace |
| Rendered rows / columns per datatable | Yes | Static, against the published guidance |
| **Minified, platform-served bundle size** | **No** | The platform compiles and serves LWC; there is no local minified artefact to measure |
| LCP / INP / CLS on a Lightning page | Partly | DevTools and RUM in the browser; **not** from a public CrUX dataset for an authenticated org |

Two consequences that most budget manifests get wrong:

1. **"Minified KB" is not a number you have.** Salesforce compiles and serves the
   component; `sfdx` does not emit a minified artefact you can weigh. Budget
   *source* bytes plus transitive imports, and treat the transferred size as
   something you observe in DevTools rather than gate on.
2. **CrUX has no field data for your org.** The Chrome UX Report covers public
   origins. A Lightning Experience org behind authentication is not in it. Field
   data for an internal app comes from your own RUM, or it does not exist —
   Experience Cloud public sites are the exception where CrUX genuinely applies.

Budget what you can measure. A manifest full of numbers nobody can produce is
how budgets get quietly abandoned.

---

## Example 1 — WRONG vs RIGHT: the budget manifest

### WRONG — plausible, unenforceable

```yaml
components:
  accountOverview:
    maxMinifiedKb: 40        # (1) no minified artefact exists to measure
    maxWireAdapters: 3
pages:
  Account_Record_Page:
    lcp: 2500                # (2) measured how, and by whom?
    inp: 200                 # (3) same
    source: crux             # (4) CrUX has no data for an authenticated org
```

Every row reads like a budget and none of them can fail a build.

### RIGHT — every row has an owner, a measurement method, and a gate

```yaml
# budgets/lwc-budgets.yaml
#
# Every entry states HOW it is measured and WHERE it is enforced.
# A row with no `gate` is documentation, not a budget — mark it explicitly.

version: 1
reviewed: 2026-08-14
next_review: 2026-11-14

defaults:
  # Applied to any component without an explicit entry. Deliberately generous:
  # a default that everything violates teaches people to ignore the gate.
  max_source_bytes: 20480          # 20 KB of authored JS + HTML + CSS
  max_transitive_bytes: 61440      # 60 KB including imported modules
  max_wire_adapters: 3
  max_imperative_per_action: 1

components:

  accountOverview:
    owner: accounts-team
    hosted_on: [Account_Record_Page]
    above_the_fold: true
    max_source_bytes: 30720
    max_transitive_bytes: 92160
    max_wire_adapters: 3
    max_imperative_per_action: 1
    gate: ci-blocking
    waiver:
      # Expiring waivers only. A waiver with no expiry is a raised budget
      # that nobody agreed to raise.
      id: PERF-412
      reason: "Q3 quote widget adds 8 KB; refactor tracked in PERF-455."
      expires: 2026-09-30
      approved_by: platform-architecture

  productCatalog:
    owner: commerce-team
    hosted_on: [Product_Catalog_App_Page, LWR_Storefront]
    above_the_fold: true
    max_source_bytes: 40960
    max_transitive_bytes: 122880
    max_wire_adapters: 2
    max_imperative_per_action: 1
    gate: ci-blocking

  adminUtilityPanel:
    owner: platform-team
    hosted_on: [Admin_Utility_Bar]
    above_the_fold: false
    gate: warn-only            # internal tool; visible, not blocking
    note: "Deliberately unbudgeted. Revisit if it moves above the fold."

pages:

  # Experience Cloud public site: CrUX genuinely applies here.
  LWR_Storefront:
    owner: commerce-team
    audience: public
    field_data_source: crux
    lcp_p75_ms: 2500
    inp_p75_ms: 200
    cls_p75: 0.1
    gate: monitor-alert        # trend alert, never a PR gate
    alert_after_days: 3

  # Internal Lightning page: no public field data exists.
  Account_Record_Page:
    owner: accounts-team
    audience: internal-authenticated
    field_data_source: none
    lab_check: "DevTools Performance trace, 4x CPU throttle, seeded sandbox"
    lab_lcp_ms: 3000           # LAB number. Not comparable to a field p75.
    gate: manual-pre-release
    note: >
      Salesforce owns most of this page. The budget covers the
      component-attributable portion; see gotcha 2.

datatables:
  # The published datatable guidance, made enforceable.
  auditLogViewer:
    max_client_rows: 1000
    max_columns: 5
    max_rows_per_request: 50
    gate: ci-blocking
```

### The four properties that make it enforceable

- **Every row names a `gate`.** `ci-blocking`, `monitor-alert`,
  `manual-pre-release`, or `warn-only`. A row with no gate is documentation and
  should say so.
- **Lab and field numbers are labelled and never compared.** A lab LCP under CPU
  throttling and a field p75 are different quantities; putting them in the same
  column produces arguments rather than fixes.
- **Waivers expire.** Without an expiry, a waiver is a permanent budget increase
  that nobody approved.
- **Defaults are generous.** A default every component violates on day one
  teaches the team to ignore the gate, and the gate never recovers.

---

## Example 2 — The CI check, including transitive imports

Bundle-size checks that measure only the leaf file are the common failure: a
2 KB component importing 60 KB of shared utilities passes while a self-contained
20 KB one fails.

```python
#!/usr/bin/env python3
"""
ci/check_lwc_budgets.py — enforce budgets/lwc-budgets.yaml.

Stdlib only, deliberately: this runs before dependencies are installed and
must not become a build dependency of its own.

Measures SOURCE bytes. The platform compiles and serves LWC, so there is no
local minified artefact; source bytes plus the transitive graph is the honest
proxy and it is stable release to release.
"""
import json
import os
import re
import sys

LWC_ROOT = "force-app/main/default/lwc"
COUNTED_EXT = (".js", ".html", ".css")

# `import X from 'c/moduleName'` — the only import form that pulls in another
# LWC bundle. @salesforce/* and lightning/* are platform-provided and are not
# part of your shipped weight.
LOCAL_IMPORT = re.compile(r"""from\s+['"]c/([A-Za-z0-9_]+)['"]""")
WIRE_DECORATOR = re.compile(r"^\s*@wire\s*\(", re.MULTILINE)


def bundle_files(name):
    path = os.path.join(LWC_ROOT, name)
    if not os.path.isdir(path):
        return []
    return [
        os.path.join(path, f)
        for f in os.listdir(path)
        if f.endswith(COUNTED_EXT)
    ]


def source_bytes(name):
    return sum(os.path.getsize(f) for f in bundle_files(name))


def local_imports(name):
    found = set()
    for f in bundle_files(name):
        if not f.endswith(".js"):
            continue
        with open(f, encoding="utf-8") as fh:
            found.update(LOCAL_IMPORT.findall(fh.read()))
    return found


def transitive_bytes(name, seen=None):
    """Total source bytes of this bundle plus everything it imports.

    The `seen` set both dedupes shared modules and terminates on the circular
    imports that LWC permits at module level.
    """
    seen = seen if seen is not None else set()
    if name in seen:
        return 0
    seen.add(name)
    total = source_bytes(name)
    for dep in local_imports(name):
        total += transitive_bytes(dep, seen)
    return total


def wire_count(name):
    total = 0
    for f in bundle_files(name):
        if f.endswith(".js"):
            with open(f, encoding="utf-8") as fh:
                total += len(WIRE_DECORATOR.findall(fh.read()))
    return total


def main(manifest_path):
    with open(manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)          # YAML converted upstream; see note

    defaults = manifest.get("defaults", {})
    failures, warnings = [], []

    for name, spec in manifest.get("components", {}).items():
        gate = spec.get("gate", "ci-blocking")
        if gate == "warn-only":
            sink = warnings
        elif gate != "ci-blocking":
            continue                       # monitor / manual gates run elsewhere
        else:
            sink = failures

        waiver = spec.get("waiver")
        checks = [
            ("source bytes", source_bytes(name),
             spec.get("max_source_bytes", defaults.get("max_source_bytes"))),
            ("transitive bytes", transitive_bytes(name),
             spec.get("max_transitive_bytes", defaults.get("max_transitive_bytes"))),
            ("wire adapters", wire_count(name),
             spec.get("max_wire_adapters", defaults.get("max_wire_adapters"))),
        ]

        for label, actual, limit in checks:
            if limit is None or actual <= limit:
                continue
            msg = f"{name}: {label} {actual} > {limit}"
            if waiver:
                warnings.append(f"{msg}  [WAIVED {waiver['id']} until {waiver['expires']}]")
            else:
                sink.append(msg)

    for w in warnings:
        print(f"WARN  {w}")
    for f in failures:
        print(f"FAIL  {f}")

    # Report every failure before exiting. Failing on the first one means the
    # team fixes them one build at a time.
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "budgets/lwc-budgets.json"))
```

### Two design notes

- **Reporting all failures before exiting** matters more than it sounds. A
  fail-fast check turns a five-violation PR into five build cycles, and the team
  starts running the check locally in a loop instead of reading the manifest.
- **Waiver expiry needs its own check.** An expired waiver must fail the build,
  or "expires" is decorative. That is a four-line addition and the single most
  important one in the script.

---

## Example 3 — Wire adapters and imperative calls, measured properly

### Why the static count is not the whole story

A static `@wire` count is cheap and useful. It also misses the thing that
actually costs a user-visible round trip: an imperative Apex call fired on every
keystroke, or a wire whose reactive parameter changes on every render.

```javascript
// Static count: 1 wire. Actual network behaviour: one request per keystroke.
@wire(searchAccounts, { term: '$searchTerm' })
results;

handleInput(event) {
    this.searchTerm = event.target.value;   // reactive -> refires the wire
}
```

### The runtime check that catches it

```javascript
// __tests__/accountSearch.network.test.js
import { createElement } from 'lwc';
import AccountSearch from 'c/accountSearch';
import searchAccounts from '@salesforce/apex/AccountController.searchAccounts';

jest.mock(
    '@salesforce/apex/AccountController.searchAccounts',
    () => ({ default: jest.fn() }),
    { virtual: true }
);

const flush = () => Promise.resolve().then(() => Promise.resolve());

// advanceTimersByTime() below is a no-op unless fake timers are installed.
beforeEach(() => jest.useFakeTimers());
afterEach(() => jest.useRealTimers());

it('issues at most one Apex call per user action', async () => {
    searchAccounts.mockResolvedValue([]);
    const el = createElement('c-account-search', { is: AccountSearch });
    document.body.appendChild(el);
    await flush();

    const input = el.shadowRoot.querySelector('lightning-input');
    // Simulate typing "acme" — four keystrokes, one intended action.
    for (const value of ['a', 'ac', 'acm', 'acme']) {
        input.value = value;
        input.dispatchEvent(new CustomEvent('change'));
    }
    jest.advanceTimersByTime(400);   // past the debounce window
    await flush();

    // The budget line `max_imperative_per_action: 1`, enforced as a test.
    expect(searchAccounts).toHaveBeenCalledTimes(1);
});
```

This is the shape that turns a manifest row into a gate. `max_wire_adapters` is
checkable statically; `max_imperative_per_action` needs a test, and the test is
where the debounce regression is caught.

---

## Example 4 — Where Lightning Web Security enters the budget

LWS runs each namespace's components in its own JavaScript sandbox and uses
Proxy objects to mediate access across the boundary. The documented performance
characteristic is specific and useful:

> *"The use of proxies has a performance cost due to the extra processing
> required. This cost is negligible when there are a few thousand proxies, but as
> the number of proxies grows into the tens of thousands, the performance impact
> becomes observable."*
> — [How LWS Architecture Affects Component
> Performance](https://developer.salesforce.com/docs/platform/lightning-components-security/guide/lws-performance.html)

Two scenarios are named as the ones that degrade: **processing tens of thousands
of objects**, where each access to a host-environment object passes through a
proxy, and **instantiating large numbers of components**, because DOM operations
are expensive and LWS magnifies that relative to Lightning Locker.

The documented mitigations are equally specific: move heavy calculation to
server-side Apex, and **clone data into the component's own sandbox namespace
before processing**, converting host-owned objects into locally-owned ones.

### The budget line this produces

```yaml
  bulkRecordProcessor:
    owner: data-team
    max_objects_processed_client_side: 5000
    gate: ci-blocking
    note: >
      LWS proxy overhead becomes observable in the tens of thousands.
      Above this ceiling the work belongs in Apex. Enforced by a test that
      asserts the component rejects oversized inputs rather than
      attempting them.
```

```javascript
// The enforcement is a guard in the component, not a hope in a wiki.
const MAX_CLIENT_SIDE_OBJECTS = 5000;

processRecords(records) {
    if (records.length > MAX_CLIENT_SIDE_OBJECTS) {
        // Fail loudly at the boundary rather than degrading in the field.
        throw new Error(
            `${records.length} records exceeds the client-side budget of ` +
            `${MAX_CLIENT_SIDE_OBJECTS}. Move this aggregation to Apex.`);
    }
    // Clone into this sandbox before iterating, per the LWS guidance —
    // repeated access to host-owned objects pays the proxy cost each time.
    const local = structuredClone(records);
    return local.reduce(this.aggregate, {});
}
```

Note that the mitigation is not intuitive: cloning normally *adds* cost. Under
LWS it removes a per-access proxy traversal, so a single clone up front is
cheaper than thousands of mediated reads.

---

## Example 5 — The regression playbook, with a decision tree

An alert with no playbook produces a ticket that sits. The playbook's job is to
get from "the number moved" to a named cause in under an hour.

```text
TRIGGER
  Field p75 LCP or INP over budget for 3 consecutive days (public site), OR
  a pre-release lab trace regresses >20% vs the previous release.

STEP 1 — Is it us?
  Compare against a page in the same org with none of our components.
  Both regressed  -> platform or org-wide change (a release, a new
                     org-wide script, a Lightning page layout change).
                     Escalate; do not refactor a component.
  Only ours       -> continue.

STEP 2 — What changed?
  Diff the budget report between the two releases:
    source bytes up      -> code was added; which PR?
    transitive bytes up, source flat
                         -> a shared module grew, or a new import was added.
                            This is the case a leaf-only budget misses.
    wire count up        -> a new round trip on first paint.
    neither moved        -> continue to step 3.

STEP 3 — Is it data, not code?
  Row counts, record sizes, and related-list volumes grow without any
  deployment. Check the rendered row count against the datatable budget
  (1,000 rows / 5 columns) before assuming a code cause.

STEP 4 — Is it LWS proxy pressure?
  Did the component start processing a materially larger collection?
  Tens of thousands of objects is where proxy overhead becomes observable.
  Fix: move the aggregation to Apex, or clone into the local sandbox once.

STEP 5 — Fix, re-measure, and update the budget.
  If the new number is the correct one, RAISE the budget deliberately with
  an approver — do not leave a permanently red gate. A gate that is always
  red is a gate that is always ignored.
```

Step 3 is the one teams skip. Performance regressions with no corresponding code
change are usually data-volume regressions, and refactoring a component is the
wrong response to a list that quietly grew from 200 rows to 4,000.
