## Well-Architected Notes — Flow Element Naming Conventions

## Relevant Pillars

- **Operational Excellence** — the on-call admin reading a fault email at
  3 AM should be able to identify the failing element from its API Name
  alone, without opening Flow Builder. `Element "Get_Records_3" failed` is
  hostile to operations; `Element "Get_OpenCasesByOwner" failed` is
  diagnostic. Naming is the cheapest observability investment in the entire
  Flow toolkit. This pillar also captures the maintainability dimension:
  six months after authoring, a different admin must be able to read the
  Flow without re-reading every formula and outcome rule to understand
  intent. Canonical naming makes the diagram self-documenting.

- **Reliability** — strong Decision outcome names eliminate a class of
  silent routing bugs. When two outcomes are both named `Yes` and an editor
  re-orders them in Flow Builder, runtime routing changes silently because
  Salesforce evaluates outcomes in the order they appear in XML. Distinct,
  business-readable outcome names eliminate this fragility.

- **Performance** — naming has **no** runtime performance impact. Flow
  Builder API Names are resolved at compile time (interview load), not
  evaluated per-record. Do not let "what if a long name is slower" be a
  reason to keep `Decision_3` over `Decision_HasActiveContract` — there is
  no performance argument here.

- **Security** — naming is generally orthogonal to security. One narrow
  exception: do not encode sensitive business logic or PII field names into
  element API Names that appear in fault emails sent to a broad alias
  (e.g. don't name a decision `Decision_IsCustomerOnDoNotMarketList` if the
  fault email goes to a non-internal recipient). Prefer functional names.

- **Scalability** — no direct impact. Naming scales linearly with the size
  of the Flow portfolio: it is precisely the orgs with hundreds of flows
  where canonical naming pays the largest dividend.

---

## Architectural Tradeoffs

The core tradeoff is **upfront discipline vs downstream archaeology cost**.

- **Pay now (canonical naming during authoring):** every element name is
  designed once. Authors may spend an extra 30 seconds per element. Subflow
  contracts are documented at creation time. Process Builder migrations
  include a rename pass.
- **Pay later (let auto-generated names ship):** every fault email, every
  Git diff review, every audit, every onboarding session, and every refactor
  pays a re-discovery tax. The cost compounds with every flow added to the
  portfolio.

Closely related: the **rename-vs-keep tradeoff for legacy flows.**
Renaming an element on an existing active flow carries non-zero risk
(formula references, parent subflows). The rule from the SKILL is:

- High-risk surfaces (Subflow inputs/outputs, Choice resources bound to
  picklists) → bump version per `flow-versioning-strategy`, do not rename
  in place.
- Low-risk surfaces (internal elements with no formula references) → safe
  to rename in a routine maintenance pass.

---

## Anti-Patterns

1. **Auto-generated names left in production.** `Decision_1`,
   `Get_Records_3`, `myWaitEvent_4` survive into production because nobody
   renamed them at authoring time. Every downstream consumer (fault emails,
   ops dashboards, the next developer) pays the cost. Fix: enforce a
   naming-conformance check in the deployment pipeline (regex-grep Flow XML
   for `_\d+$` element names and fail the build).

2. **Bare `Yes` / `No` Decision outcomes.** Two flows both have a
   `Decision_<X>` with outcomes `Yes` and `No`. The fault email reports
   `Decision_<X>.outcome[Yes]` failed — but which Decision in which Flow,
   and what was the question? Strong outcome names are the cure.

3. **Renaming Subflow inputs in place.** The author "tidies up"
   `inputAccountId` → `inputAcctId` on an active subflow. Six parent flows
   break at the next interview. Always use the version-bump path.

4. **Encoding redundant information in both Label and API Name.** If
   Label = "Get Open Cases by Owner" and API Name = `Get_Open_Cases_By_Owner`,
   you have created two parallel sources of truth. The API Name should be
   the canonical short form (e.g. `Get_OpenCasesByOwner`); the Label can be
   a longer human sentence.

5. **Skipping the rename pass on Process Builder migrations.** The
   conversion succeeds, the flow is deployed, the auto-names ship. Now the
   Flow is technically harder to maintain than the Process Builder it
   replaced. Treat the rename pass as a non-negotiable step of the
   migration plan.

---

## Official Sources Used

- Salesforce Help — Flow Builder Element Reference: https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements.htm
- Salesforce Help — Flow Concepts and Terms: https://help.salesforce.com/s/articleView?id=platform.flow_concepts_terms.htm
- Salesforce Architects — Well-Architected Operational Excellence: https://architect.salesforce.com/well-architected/trusted/resilient
- Salesforce Architects — Well-Architected Resilience: https://architect.salesforce.com/well-architected/trusted/resilient
- Salesforce Help — Subflow Element: https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_subflow.htm
