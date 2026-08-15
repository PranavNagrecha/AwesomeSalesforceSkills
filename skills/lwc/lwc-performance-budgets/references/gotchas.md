# Gotchas — LWC Performance Budgets

---

## 1. There is no minified bundle to measure

**What happens:** the manifest specifies `maxMinifiedKb: 40`. Nobody can produce
the number, the check is never written, and the row becomes decoration.

**Why:** Salesforce compiles and serves Lightning Web Components. `sf project
deploy` sends source; there is no local build step emitting a minified artefact
you can weigh, the way a webpack or Vite project would.

**How to avoid:** budget **source bytes** plus **transitive import bytes**. Both
are measurable in CI with stdlib code, stable across releases, and correlate with
what ships. Observe the transferred size in DevTools when you want the real
number, but do not gate on a figure your pipeline cannot produce.

---

## 2. CrUX has no field data for an authenticated org

**What happens:** the budget names CrUX as the field-data source for a Lightning
record page. The query returns nothing, and the LCP/INP rows never get populated.

**Why:** the Chrome UX Report covers public origins with sufficient traffic. A
Lightning Experience org behind authentication is not one.

**How to avoid:** split the manifest by audience. Public Experience Cloud sites
genuinely have CrUX data and can carry field budgets. Internal Lightning pages
have lab measurements from a DevTools trace against a seeded sandbox, or your own
RUM instrumentation, or nothing — and "nothing" is an honest entry that stops
someone building a dashboard on an empty dataset.

---

## 3. Lab numbers and field p75s are different quantities

**What happens:** a lab trace under 4× CPU throttling shows LCP of 3.1s. The
field budget says 2.5s. Somebody opens a performance ticket for a component that
is fine.

**Why:** a throttled synthetic run models a slow device deliberately. A field p75
is the 75th percentile of a real population on a mixture of devices and
networks. They are not comparable, and neither is wrong.

**How to avoid:** label every number `lab_` or `field_` in the manifest and never
put them in the same column. Lab numbers detect *regression against the previous
lab run*; field numbers describe *experience*. Both are useful; comparing them
produces arguments instead of fixes.

---

## 4. Measuring only the leaf file misses the real weight

**What happens:** a 2 KB component passes the budget while pulling in 60 KB of
shared utilities and i18n catalogues. A self-contained 20 KB component fails.

**How to avoid:** walk the `from 'c/moduleName'` import graph and sum. Two
details matter: dedupe shared modules with a `seen` set, and let that same set
terminate the walk on circular imports, which LWC permits at module level.

`@salesforce/*` and `lightning/*` imports are platform-provided and are not part
of your shipped weight — do not count them.

---

## 5. Most of a Lightning record page is not yours

**What happens:** a component's LCP budget is set at 2.5s and the page never gets
there, because the platform's own chrome, the highlights panel, and four other
teams' components dominate the timeline.

**How to avoid:** budget the **component-attributable** portion, not the page
total, for anything hosted on a platform-composed page. Concretely: measure the
delta between the page with your component and the page without it. That number
is actionable; the page total is a shared outcome you cannot unilaterally move.

Keep a page-level budget for pages you fully control — LWR sites and custom app
pages — where the total genuinely is attributable.

---

## 6. LWS proxy overhead is a real budget line at volume

**What happens:** a component that aggregated 2,000 records happily is pointed at
40,000 and becomes visibly slow, with no code change to the aggregation.

**The documented behaviour:** LWS runs each namespace in its own sandbox and
mediates cross-boundary access with Proxy objects. *"This cost is negligible when
there are a few thousand proxies, but as the number of proxies grows into the
tens of thousands, the performance impact becomes observable."* The two named
degradation scenarios are processing tens of thousands of objects, and
instantiating large numbers of components
([How LWS Architecture Affects Component
Performance](https://developer.salesforce.com/docs/platform/lightning-components-security/guide/lws-performance.html)).

**How to avoid:** a budget line for client-side collection size, enforced as a
guard in the component that throws rather than degrading. The documented
mitigations are to move heavy calculation to Apex, and to **clone the data into
the component's own sandbox before processing** — counter-intuitive, because
cloning normally adds cost, but it converts thousands of mediated reads into one.

---

## 7. Wire count is a static proxy for a runtime behaviour

**What happens:** a component has one `@wire` and issues a request per keystroke,
because the wire's reactive parameter is bound to an input value.

**How to avoid:** keep the static wire count as a cheap structural check, and add
a Jest test asserting calls-per-user-action with mocked Apex and advanced timers.
The test is what catches a removed debounce; the static count never will.

`@wire` uses the Lightning Data Service cache, so a repeated call may be served
locally — but the **first** render still pays every round trip, which is exactly
the paint you are budgeting.

---

## 8. A default that everything violates trains the team to ignore the gate

**What happens:** the budget ships with tight defaults. Forty components fail on
day one. The gate is disabled "until we clean up", and never re-enabled.

**How to avoid:** set the initial default from the observed distribution — around
the current 75th percentile — so most components pass immediately and the
outliers are visible. Then tighten quarterly toward the observed 90th percentile.
A budget's first job is to stop things getting worse; ratcheting comes second.

---

## 9. A gate with no waiver path gets disabled under release pressure

**What happens:** a genuinely necessary 8 KB feature blocks a release. Someone
comments out the CI step. It stays commented out.

**How to avoid:** an explicit waiver with an id, a reason, an approver, and an
**expiry**. And a separate check that fails the build on an *expired* waiver —
without it, "expires" is decorative and every waiver is permanent. That check is
four lines and is the most important part of the mechanism.

---

## 10. Fail-fast turns one bad PR into five builds

**What happens:** the checker exits on the first violation. A PR with five
violations takes five CI cycles to clear, and the team starts running the check
in a local loop rather than reading the manifest.

**How to avoid:** collect every violation, print them all, then exit non-zero
once. The cost is a few lines; the benefit is that a developer sees the whole
problem in one pass.

---

## 11. Nobody reviews the manifest, so it encodes an obsolete architecture

**What happens:** two years on, the budget still lists components that were
deleted, omits the twelve added since, and its numbers reflect a page layout that
no longer exists.

**How to avoid:** `reviewed` and `next_review` dates in the manifest itself, plus
a check that fails (or warns loudly) when `next_review` has passed. Quarterly is
a reasonable cadence. A budget file with no review date is a snapshot pretending
to be a policy.

Add a completeness check too: any LWC bundle with no manifest entry and no
default coverage should warn. Otherwise new components are silently unbudgeted,
which is where the growth goes.

---

## 12. Performance regressions with no code change are usually data volume

**What happens:** the alert fires, the team diffs the release, nothing relevant
changed, and the investigation stalls.

**Why:** row counts, related-list sizes, and record widths grow continuously
without any deployment. A datatable that rendered 200 rows at launch renders
4,000 a year later, and the published guidance is 1,000 rows and 5 columns.

**How to avoid:** put "check rendered row counts against the datatable budget"
ahead of "diff the code" in the regression playbook. Refactoring a component is
the wrong response to a list that quietly grew.

---

## 13. Lighthouse against a stripped-down harness measures the harness

**What happens:** Lighthouse CI runs against a local jsdom or a bare LWR page
containing only the component. It reports a 98 and tells you nothing about the
Lightning page the component actually lives on.

**How to avoid:** either run against a preview sandbox with representative data
and the real page composition, or drop the synthetic page score and gate on the
things that are genuinely static — source bytes, transitive weight, wire count,
row and column counts. The second option is less impressive and more honest, and
it is the one that keeps working.

---

## 14. Budgeting bytes while ignoring images

**What happens:** JavaScript is meticulously budgeted at 30 KB and the component
renders an unoptimised 1.2 MB hero image from a static resource.

**How to avoid:** include image weight and request count in the manifest for any
component that renders media, and check static-resource sizes in the same CI
pass. For most components the largest single byte contribution is not the code.

---

## 15. A budget with no named owner

**What happens:** the gate fails. Nobody knows who decides whether to fix the
component or raise the limit, so the PR sits until someone disables the check.

**How to avoid:** every manifest entry names an owning team, and the waiver
mechanism names an approver. A budget is a negotiated constraint between two
parties; with only one party it is a rule that will be routed around.
