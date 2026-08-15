# LLM Anti-Patterns — LWC Performance Budgets

---

## Anti-Pattern 1: Budgeting a minified bundle size that does not exist

**What the LLM generates:**

```yaml
components:
  accountOverview:
    maxMinifiedKb: 40
```

plus a CI step reading it "from the build output".

**Why it happens:** minified bundle size is *the* canonical front-end budget
metric, and every webpack, Vite, and Rollup project produces it. The model
transfers the metric without modelling the fact that Salesforce compiles and
serves LWC — there is no local build emitting an artefact to weigh.

**Correct pattern:** budget **source bytes** and **transitive import bytes**.
Both are measurable in CI with stdlib code and stable across releases. Observe
the transferred size in DevTools when you want the real number; do not gate on a
figure the pipeline cannot produce.

**Detection hint:** the word "minified" in a Salesforce budget manifest, or a CI
step referencing `dist/` or `build/`.

---

## Anti-Pattern 2: CrUX as the field-data source for an internal org

**What the LLM generates:** a monitoring design that queries the CrUX API for
`https://myorg.lightning.force.com` LCP and INP.

**Why it happens:** CrUX is the standard field-data source for Core Web Vitals
and the model has seen thousands of examples. That it covers *public* origins
with sufficient traffic is a qualifier, not a headline.

**Correct pattern:** split by audience. Public Experience Cloud sites genuinely
have CrUX data. Internal Lightning pages have lab traces, your own RUM, or
nothing — and recording "field_data_source: none" is an honest entry that stops
someone building a dashboard on an empty dataset.

**Detection hint:** CrUX named as the source for anything behind authentication.

---

## Anti-Pattern 3: A single global LCP number

**What the LLM generates:** "budget LCP < 2.5s across the application."

**Why it happens:** 2.5s is the published "good" threshold for LCP and reads as a
universal target. Per-page-template budgeting requires knowing the page
inventory, which a general answer does not have.

**Correct pattern:** budget per page template, and only where the total is
attributable to you. On a platform-composed Lightning record page, most of the
timeline belongs to Salesforce and other teams — budget the **delta** your
component introduces. Keep page totals for LWR sites and custom app pages you
fully control.

**Detection hint:** one LCP figure applied to every page in the org.

---

## Anti-Pattern 4: Leaf-file-only size measurement

**What the LLM generates:**

```bash
find force-app/main/default/lwc -name '*.js' -size +50k
```

as the bundle-size check.

**Why it happens:** file size is trivially available and the import graph is not.
The model produces the measurable proxy rather than the correct metric.

**Correct pattern:** walk the `from 'c/moduleName'` graph and sum, deduping
shared modules with a `seen` set that also terminates circular imports. A 2 KB
component importing 60 KB of utilities is the case a leaf check is blind to, and
it is the common one.

Exclude `@salesforce/*` and `lightning/*` — platform-provided, not your weight.

**Detection hint:** a size check with no import parsing.

---

## Anti-Pattern 5: A hard gate with no waiver path

**What the LLM generates:** a CI step that fails the build on any violation, full
stop, presented as discipline.

**Why it happens:** the request is for enforcement and an unconditional gate is
maximal enforcement. The organisational failure mode — the gate being commented
out during a release crunch and never restored — is a second-order consequence
outside the frame.

**Correct pattern:** waivers with an id, a reason, an approver, and an **expiry**,
plus a separate check that fails on an expired waiver. Without that second check
"expires" is decorative and every waiver is permanent. Four lines, and it is the
part that keeps the gate alive.

**Detection hint:** an enforcement design with no exception mechanism, or a
waiver format with no expiry field.

---

## Anti-Pattern 6: Tight defaults on day one

**What the LLM generates:** "cap every component at 30 KB and 2 wire adapters" as
the starting configuration.

**Why it happens:** the numbers are reasonable in the abstract, and the model has
no visibility into the current distribution.

**Correct pattern:** derive the initial default from the observed distribution —
roughly the current 75th percentile — so most components pass immediately and the
outliers stand out. Then ratchet quarterly toward the 90th. Forty failures on day
one gets the gate disabled, and a disabled gate never comes back.

**Detection hint:** specific caps proposed with no baseline measurement step
preceding them.

---

## Anti-Pattern 7: Omitting Lightning Web Security from the performance model

**What the LLM generates:** a budget covering bytes, wires, and Core Web Vitals,
with no mention of the runtime environment.

**Why it happens:** LWS is filed under security in the documentation and in the
model's associations. Its performance characteristics are a separate page that
does not surface for a performance question.

**Correct pattern:** LWS runs each namespace in its own sandbox and mediates
cross-boundary access with proxies. The documented behaviour is that proxy cost
is *"negligible when there are a few thousand proxies"* and *"observable"* in the
tens of thousands, with two named degradation scenarios: processing tens of
thousands of objects, and instantiating large numbers of components. That is a
budget line — a ceiling on client-side collection size, enforced as a guard that
throws rather than degrades.

**Detection hint:** a performance budget for LWC with no collection-size or
component-count line.

---

## Anti-Pattern 8: Static wire count as the whole round-trip budget

**What the LLM generates:** a `grep -c '@wire'` check, presented as the network
budget.

**Why it happens:** it is the one countable, greppable thing, and it does
correlate. The runtime behaviour — a reactive wire parameter refiring per
keystroke — is invisible to static analysis.

**Correct pattern:** keep the static count as a structural check and add a Jest
test asserting calls-per-user-action with mocked Apex and advanced timers. The
test is what catches a removed debounce; a count of decorators never will.

**Detection hint:** no runtime network assertion anywhere in the budget design.

---

## Anti-Pattern 9: Lighthouse against a synthetic harness

**What the LLM generates:** a Lighthouse CI config pointed at `localhost` or a
minimal page containing only the component under test.

**Why it happens:** Lighthouse CI is the standard tooling answer and it is easy
to automate. That the harness is not the Lightning page — with its chrome, other
components, and platform JavaScript — is a validity question rather than a
configuration one.

**Correct pattern:** either run against a preview sandbox with representative
data and the real page composition, or drop the synthetic score entirely and gate
on what is genuinely static: source bytes, transitive weight, wire count, row and
column counts. The second is less impressive and keeps working.

**Detection hint:** a Lighthouse assertion block with no statement of what it is
running against.

---

## Anti-Pattern 10: A manifest with no review date and no owners

**What the LLM generates:** a clean YAML file of components and limits.

**Why it happens:** the deliverable requested was a budget, and a budget is a
file. Ownership and review cadence are process rather than artefact.

**Correct pattern:** `reviewed` and `next_review` dates in the manifest, a check
that warns loudly once `next_review` passes, and an owning team on every entry
plus an approver on every waiver. A gate with no owner fails, nobody knows who
decides, and it gets disabled. A budget with no review date encodes an
architecture that will be obsolete within a year.

**Detection hint:** no dates and no team names anywhere in the manifest.

---

## Anti-Pattern 11: Code-only regression triage

**What the LLM generates:** a playbook that goes straight from "alert fired" to
"profile the component and diff the code".

**Why it happens:** performance regression implies a code change in the model's
priors, because in most systems it is one.

**Correct pattern:** check data volume first. Row counts, related-list sizes, and
record widths grow continuously without any deployment, and the published
datatable guidance is 1,000 rows and 5 columns. Also check whether an unrelated
page regressed too — if it did, the cause is platform or org-wide and refactoring
a component is the wrong response.

**Detection hint:** a playbook with no data-volume step and no "is it us?" step.

---

## Anti-Pattern 12: Budgeting JavaScript while ignoring images

**What the LLM generates:** a byte budget covering `.js` and nothing else.

**Why it happens:** "bundle size" means JavaScript in front-end discourse, and
static resources are a Salesforce-specific delivery mechanism outside that frame.

**Correct pattern:** for any component rendering media, include image weight and
request count, and check static-resource sizes in the same CI pass. The largest
single byte contribution is frequently not the code.

**Detection hint:** a manifest with byte limits and no image or static-resource
line for components that clearly render images.
