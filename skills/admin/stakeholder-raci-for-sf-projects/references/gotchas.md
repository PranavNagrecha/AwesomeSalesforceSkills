# Gotchas — Stakeholder RACI for Salesforce Projects

Non-obvious project-governance behaviors that cause real production problems on Salesforce projects.

## Gotcha 1: More than one A per row

**What happens:** Two stakeholders carry A on the same row "to share accountability." When they disagree, the project blocks. Each assumes the other will decide. The decision waits weeks until escalation.

**When it occurs:** Most often on cross-functional rows — data model, integration boundary, security on PHI/PII data — where two leaders have legitimate authority claims.

**How to avoid:** Enforce the one-A rule at the matrix level (the `check_raci.py` script catches this). If two leaders both want A, escalate to the sponsor or steerco to pick one — and document the loser as C, not A. The shared-A pattern is a polite fiction that costs sprints.

---

## Gotcha 2: A on a Consulted role

**What happens:** A row lists a stakeholder as both A and C. The role is being consulted on its own decision. C means "two-way input before the decision" — but if you are the decision-maker, there is no second party to consult.

**When it occurs:** When the matrix author copies a "C" into the column that already has "A" — usually because they ran out of named individuals and reused one across roles.

**How to avoid:** Never combine A and C in the same cell. The checker script flags this. Underlying root cause is usually that two roles are filled by one person; if that is the reality, document it explicitly ("Person X holds both Security Architect and Integration Architect roles") rather than encoding it as A/C in a cell.

---

## Gotcha 3: Missing process owner

**What happens:** No process owner is named for the affected business function. The data steward holds A on data model decisions by default — but they don't know which fields the business actually uses. The model gets built; adoption fails because the model doesn't fit the work.

**When it occurs:** On enhancement projects where the original implementation didn't name a process owner and the role atrophied, or on greenfield projects where the sponsor hasn't yet identified a director-level owner of the affected function.

**How to avoid:** Refuse to publish the matrix until the process owner column has a named individual. This is a project risk to escalate to the sponsor, not a placeholder to fill in later. If the sponsor cannot name one, the project is not ready to start.

---

## Gotcha 4: Escalation rule without a time-box

**What happens:** "Escalates to sponsor if blocked" is written in the escalation rule, but no number of days is specified. The team waits indefinitely for the A to decide; the sponsor never gets pinged because nobody knows when the clock has run out.

**When it occurs:** When the matrix is built from a generic project template that omits the time-box column.

**How to avoid:** Every escalation rule must have three parts: trigger, target, time-box. Default time-boxes — 1 business day for deployment, 3 business days for security and automation tier, 5 business days for data model and integration, 10 business days for license tier. Without a time-box the rule is decorative.

---

## Gotcha 5: RACI that ignores the AppExchange owner

**What happens:** A managed package (CPQ, FSL, NPSP, Conga, DocuSign, OmniStudio, Marketing Cloud Account Engagement) is in scope but no AppExchange owner column exists. The project makes data-model decisions that conflict with the package's namespace constraints; the next package release breaks them.

**When it occurs:** When the implementation team treats a managed package as "just another set of metadata" instead of a vendor-controlled namespace with its own release cadence.

**How to avoid:** Add an AppExchange owner column for every managed package in scope. The owner holds A on decisions that touch the package's namespace (renaming an SBQQ field, suppressing a vlocity validation, customizing an FSL flow). Their A is non-negotiable because the package vendor will overwrite their decisions on the next release if they aren't consulted.

---

## Gotcha 6: RACI built once and never reviewed

**What happens:** The matrix is built during discovery and never touched again. By UAT, three named individuals have left, two roles have been re-org'd, and the actual escalation paths bear no resemblance to the document. The matrix becomes a wall poster.

**When it occurs:** On long projects (6+ months), on projects with org-design changes, and on projects where the sponsor changes mid-stream.

**How to avoid:** Version-lock the matrix per phase (discovery, build, UAT, hypercare). Each phase requires a re-review with the sponsor before phase exit. Add the next-review date as a field on the matrix itself; if the date passes without a review, the matrix is stale and downstream agents should treat it as advisory only.

---

## Gotcha 7: Implementation partner holds A past hypercare

**What happens:** During build, the SI's lead architect carries A on integration and security because they own the design. Hypercare ends; the SI rolls off; nobody at the customer holds A on those rows. Every change request after hypercare blocks until the partner is re-engaged at T&M rates.

**When it occurs:** On any consulting-led implementation where the customer hasn't named an internal counterpart for each architect role.

**How to avoid:** Include a "transfer date" field on every cell where the partner holds A. By the transfer date, A must move to a named customer employee — even if the customer employee is junior. Knowledge transfer sessions during hypercare exist exactly to prepare them. If the customer cannot staff to receive A, raise it to the sponsor as a post-go-live risk.

---

## Gotcha 8: Compliance officer downgraded to C on regulatory rows

**What happens:** Project teams find compliance review cycles slow and assign them as C "to keep them in the loop." The privacy officer is invited to meetings but does not hold the decision. The build ships; audit fires; remediation costs more than building it right would have.

**When it occurs:** On HIPAA, FINRA, PCI, GDPR, and SOX projects where compliance is treated as a checkpoint rather than a decision-maker.

**How to avoid:** Compliance officer must hold A on the regulatory-control rows — audit trail, retention, data subject rights, BAA, PHI/PII access, financial controls. Compliance is C on rows that are non-regulated. Splitting the data-model and security rows into "regulated" and "non-regulated" sub-rows is the cleanest way to scope compliance's A.
