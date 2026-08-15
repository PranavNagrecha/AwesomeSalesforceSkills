# Well-Architected — LWC Performance Budgets

## Relevant Pillars

### Performance Efficiency

A budget makes performance a **deliverable with a gate**, rather than a
post-launch regression hunt. Its first job is to stop things getting worse; the
ratchet toward better comes second, and inverting that order kills the gate
before it can help.

What distinguishes a Salesforce budget from a generic front-end one is the set of
metrics that are actually available:

| Metric | Available | Why |
|---|---|---|
| Source bytes, transitive import bytes | Yes | Static, stdlib-checkable |
| `@wire` count, imperative calls per action | Yes | Static count plus a Jest assertion |
| Datatable rows and columns | Yes | Against published guidance: 1,000 rows / 5 columns |
| Client-side collection size | Yes | LWS proxy cost is observable in the tens of thousands |
| Minified bundle size | **No** | The platform compiles and serves LWC; no local artefact |
| CrUX field data | Public sites only | Authenticated orgs are not in the dataset |

Budgeting what you cannot measure is how manifests become decoration. Half the
work in this skill is deleting the rows that look right and cannot fail.

### Operational Excellence

A gate that fires is a gate that will be routed around unless three things are in
place: a named owner per entry, an approver for exceptions, and expiring waivers
with a check that fails on expiry. Without the last one, "expires" is decorative
and every waiver is a permanent, unapproved budget increase.

The manifest also needs its own review cadence — `reviewed` and `next_review`
dates, with a warning once the date passes. A budget file with no review date
encodes an architecture that will be obsolete within a year, and a completeness
check (any bundle with no entry and no default coverage warns) is what stops new
components being silently unbudgeted, which is exactly where growth goes.

### Reliability

The regression playbook's ordering is what makes it usable, and it is
counter-intuitive:

1. **Is it us?** Compare a page with none of your components. If both regressed,
   the cause is platform or org-wide, and refactoring a component is the wrong
   response.
2. **Did data volume change?** Row counts, related-list sizes, and record widths
   grow continuously with no deployment. Check the rendered row count against the
   datatable budget before diffing code.
3. **Did code change?** Diff the budget report between releases — transitive
   bytes rising while source bytes stay flat is the signature of a grown shared
   module, and it is the case a leaf-only budget cannot see.

Steps 1 and 2 come first because they are cheap and because they are where the
answer usually is. Most teams write the playbook starting at step 3.

### Security (as a performance input)

Lightning Web Security is a performance input, not only a security control. LWS
runs each namespace's components in its own JavaScript sandbox and mediates
cross-boundary access with Proxy objects. The documented characteristic:

> *"The use of proxies has a performance cost due to the extra processing
> required. This cost is negligible when there are a few thousand proxies, but as
> the number of proxies grows into the tens of thousands, the performance impact
> becomes observable."*

with two named degradation scenarios — processing tens of thousands of objects,
and instantiating large numbers of components — and two documented mitigations:
move heavy calculation to server-side Apex, and clone data into the component's
own sandbox before processing, converting host-owned objects into locally-owned
ones ([How LWS Architecture Affects Component
Performance](https://developer.salesforce.com/docs/platform/lightning-components-security/guide/lws-performance.html)).

The mitigation is worth noting because it inverts the usual intuition: cloning
normally adds cost, and under LWS a single clone replaces thousands of mediated
reads.

---

## Architectural Tradeoffs

### Static checks vs. synthetic page scores

| | Static (bytes, imports, wires, rows) | Lighthouse against a harness |
|---|---|---|
| Deterministic | Yes | No |
| Measures the real page | Partly (a proxy) | Only if the harness *is* the real page |
| Flake in CI | None | Common |
| Impressive in a slide | No | Yes |

Static checks are the ones that keep working. Lighthouse is worth running only
against a preview sandbox with representative data and real page composition; a
score from a stripped-down harness measures the harness. When that is not
available, dropping the synthetic score is the honest choice, not a gap.

### Lab gate vs. field alert

Lab measurements are reproducible and detect regression against the previous lab
run. Field data describes actual experience and is only available for public
origins. Run both where both exist — lab as the pre-release gate, field as a
trend alert over consecutive days. Never compare their numbers to each other;
they are different quantities and comparing them produces arguments rather than
fixes.

### Per-component vs. per-page budgets

Per-component catches the specific offender and misses emergent composition — six
components each inside budget can still produce a slow page. Per-page captures
the outcome and cannot assign responsibility, and on a platform-composed
Lightning record page most of the total is not yours anyway.

The resolution: per-component budgets everywhere, per-page budgets only for pages
you fully control (LWR sites, custom app pages), and a **component-attributable
delta** — the page with and without your component — for platform-composed pages.

### Hard gate vs. warn-only

Hard gates enforce and block delivery. Warn-only is ignored. The workable middle
is a hard gate with an expiring waiver process, plus an explicit `warn-only`
classification for components where blocking is genuinely not warranted (internal
admin tools, below-the-fold utilities). Marking those explicitly is better than
leaving them out — an omitted component is unbudgeted; a `warn-only` component is
a decision.

### Tight budgets vs. adoption

A default that most components violate on day one gets the gate disabled within a
sprint, and disabled gates do not come back. Start near the observed 75th
percentile so the outliers are the failures, then ratchet quarterly toward the
90th. The budget that ships and holds beats the budget that is correct and
switched off.

---

## Anti-Patterns

1. **Budgeting a minified size that does not exist.** The metric transfers from
   webpack projects and has no Salesforce referent.

2. **CrUX for an authenticated org.** No data exists; the row never gets
   populated and the dashboard is built on nothing.

3. **A single global LCP number.** A login screen and a record page with a
   40-field sidebar have different baselines, and neither total is fully yours.

4. **Leaf-file-only measurement.** Misses the 60 KB of shared utilities behind a
   2 KB component — the common case.

5. **A gate with no waiver, or waivers with no expiry check.** The first gets the
   gate disabled; the second makes every waiver permanent.

6. **Omitting LWS from the performance model.** Proxy overhead at collection
   volume is a documented, budgetable characteristic.

7. **Code-first regression triage.** Skips the two cheap checks — is it us, and
   did data volume grow — where the answer usually is.

8. **A manifest with no owners and no review date.** A failing gate with no owner
   gets disabled; an unreviewed manifest encodes last year's architecture.

---

## Hygiene

- Manifest carries `reviewed` and `next_review`; a check warns once the date
  passes.
- Every entry names an owning team; every waiver names an approver and an expiry.
- Expired waivers fail the build.
- The checker reports every violation before exiting, not just the first.
- A completeness check warns on any LWC bundle with no manifest entry.
- Budgets tighten quarterly toward the observed 90th percentile.

---

## Related

- `lwc/lwc-performance` — the runtime optimisation techniques a failing budget
  sends you to.
- `lwc/lwc-locker-to-lws-migration` — the sandbox model behind the proxy cost.
- `lwc/virtualized-lists` — where the datatable row and column ceilings become
  enforceable budget lines.
- `lwc/lwc-jest-testing-with-accessibility` — the harness for the
  calls-per-user-action assertion.
- `devops/ci-cd-pipeline-design` — where the gate and the waiver check live.
- `templates/lwc/jest.config.js` — canonical Jest configuration.

---

## Official Sources Used

- Improve Performance (LWC Developer Guide) — https://developer.salesforce.com/docs/platform/lwc/guide/perf-intro.html
- Best Practices for Development with Lightning Web Components — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
- Improve Datatable Performance — https://developer.salesforce.com/docs/platform/lwc/guide/data-table-performance.html
- How LWS Architecture Affects Component Performance — https://developer.salesforce.com/docs/platform/lightning-components-security/guide/lws-performance.html
- How LWS Works — https://developer.salesforce.com/docs/platform/lwc/guide/security-lwsec-architecture.html
- Dynamically Instantiate Components — https://developer.salesforce.com/docs/platform/lwc/guide/js-dynamic-components.html
- Core Web Vitals (web.dev) — https://web.dev/vitals/
- Performance Budgets 101 (web.dev) — https://web.dev/performance-budgets-101/
- Lighthouse CI — https://github.com/GoogleChrome/lighthouse-ci
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
