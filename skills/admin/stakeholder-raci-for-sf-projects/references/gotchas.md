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

---

## Gotcha 9: The sandbox refresh is approved by someone who does not own the data in it

**What happens:** The release manager schedules a Full sandbox refresh because the metadata has drifted from production. The refresh replaces the org: the environment that comes back has a different org ID, so connected tooling treats it as a new environment, and anything that lived only in the old copy — half-finished UAT evidence, a rehearsed load's error files, seeded test data, unmerged work — is gone. DevOps Center models this explicitly: it compares its stored `OrgIdentifier` against the org it connects to and, when they differ, concludes the org is a refreshed sandbox, then uses `RefreshDate` and `RefreshSourceId` to work out which work items are missing from the swapped environment (Object Reference, `DevopsEnvironment`).

**When it occurs:** Whenever the refresh row is missing from the RACI, or is assigned to the person who *performs* the refresh rather than the person who *loses* something when it happens. It bites hardest mid-UAT and mid-migration-rehearsal, when the sandbox holds evidence that exists nowhere else.

**How to avoid:** Put the refresh row in the matrix with **A** on the data owner (usually the data steward) and **R** on the release manager, and give it a trigger that names the blocking condition — unmerged work or unfinished UAT evidence present at the requested date. A Full sandbox is also where load rehearsals happen: a Full Sandbox that isn't created from a template carries its own API allocation of 5,000,000 calls in 24 hours (Salesforce App Limits Cheat Sheet), so the rehearsal that gets destroyed is not cheap to re-run.

---

## Gotcha 10: "Salesforce admin" holds A on everything

**What happens:** The matrix names one column, "Salesforce admin", and gives it **A** on data model, sharing, permissions, deployment, and data loads. Every decision now routes to the one person who cannot refuse any of them. The security model drifts toward whatever unblocked the last ticket, and when that person leaves, no other role has ever exercised a decision.

**When it occurs:** On small teams, on admin-led builds with no architect, and on matrices copied from a generic PM template where the technology column was filled in with a job title rather than a decision surface.

**How to avoid:** Split the admin column by decision, not by person — even when one person fills several roles. Write "K. Duarte holds both CRM admin lead and release manager for this phase" in the register rather than merging the columns; the split survives the re-org, the merge does not. The platform makes the same distinction: delegated administration exists precisely to hand out bounded admin authority, and a delegated administrator can customise the custom objects assigned to their group but cannot create or modify relationships on them and cannot set org-wide sharing defaults (Metadata API Developer Guide, `DelegateGroup`). If Salesforce refuses to treat "admin" as one undifferentiated authority, the matrix should not either.

---

## Gotcha 11: The integration's owner is outside the RACI

**What happens:** The middleware team, the ERP team, or a vendor owns a running integration but appears nowhere in the matrix. Their job changes consume org-wide capacity that someone else is accountable for. Bulk API 2.0 splits an ingest job into a batch per 10,000 records up to a daily maximum of 150,000,000 records, and once that limit is passed while processing, the remaining data is not processed and the job is marked failed (Bulk API 2.0 Developer Guide). Concurrent inbound requests running 20 seconds or longer are capped at 25 for production orgs and sandboxes (Salesforce App Limits Cheat Sheet). Both are shared: the load the project rehearsed can fail because of a job nobody in the matrix scheduled.

**When it occurs:** When the integration predates the project, when it is owned by a different cost centre, or when the vendor's contact is a support queue rather than a named person.

**How to avoid:** Give every running integration a named owner row in the register, and make the integration architect **A** on the integration-change activity with those owners as **C**. Include the org-wide consumers, not only the ones this project is building. `agents/integration-catalog-builder/AGENT.md` produces the inventory; the RACI is where each catalogue entry acquires a person.

---

## Gotcha 12: Release Update activation is owned by nobody

**What happens:** A Salesforce Release Update is announced with two dates — the release in which it becomes available to activate, and the release in which it is enforced whether or not anyone activated it. The Apex Developer Guide's own example follows that shape: a restriction that applies to new managed-package namespaces immediately becomes, for existing namespaces, a release update available to subscribers in Summer '26 and enforced in Summer '27. With no row in the matrix, nobody tests it, nobody schedules it, and the platform activates it on the enforcement date in the middle of a sprint. The state is not always reversible afterwards: `MyDomainSettings.useStabilizedSandboxMyDomainHostnames` corresponds to a release update enforced in Summer '20 and, as of API version 49.0, its value is always `true` regardless of what you set — so the setting can still *read* false in a stale copy while the platform behaves as enforced (Metadata API Developer Guide).

**When it occurs:** Between projects, during hypercare, and any time the RACI covers "deployment" but not "changes Salesforce makes to us". Orgs with a slow test cycle are the worst affected, because the two-release window is the whole test budget.

**How to avoid:** Make release-update activation its own activity row with **A** on the release manager, **C** on the security, integration, and data roles, and a time-box measured in releases rather than days. Pair it with a preview row: the release the update lands in is testable before it reaches production. `agents/change-impact-planner/AGENT.md` sizes the blast radius; `agents/org-health-assessor-v2/AGENT.md` reports which updates are pending.

---

## Gotcha 13: The data load is approved by the system owner instead of the data owner

**What happens:** The admin who runs Data Loader signs off the load because they operate the tool. Two platform behaviours make that the wrong signature. First, a hard delete configured through Data Loader's Bulk API option removes records immediately and they cannot be recovered from the Recycle Bin (Data Loader Guide). Second, a Bulk API 2.0 ingest job that cannot process a batch within five minutes fails it, retries up to 20 times, and then moves the whole job to Failed and stops processing the remaining data — which leaves the object in a partially loaded state that only someone who understands the records can adjudicate (Bulk API 2.0 Developer Guide).

**When it occurs:** On migration cutovers, on any "quick cleanup" load, and whenever the load is treated as an operational task rather than a decision. The gap is invisible until a rollback is needed.

**How to avoid:** Put **A** on the data owner (data steward or process owner) and **R** on whoever runs the tool, and make hard delete and any material overrun of the rehearsed row count explicit escalation triggers. Run `agents/data-loader-pre-flight/AGENT.md` before the load and `agents/data-migration-reconciler/AGENT.md` after it, and attach both outputs to the approval — the approver signs the evidence, not the intention.

---

## Gotcha 14: Delegated admin grants contradict the RACI

**What happens:** The matrix says the CRM admin lead is **A** on permission-set changes, but a `DelegateGroup` in the org lets a regional admin assign profiles and permission set groups, and log in as the users they administer. Delegated administrators can be granted assignment of profiles, permission sets, and permission set groups for specified roles and all subordinate roles, and `loginAccess` allows them to log in as users in the role hierarchy they administer, subject to org settings that may require the individual user to grant login access (Metadata API Developer Guide, `DelegateGroup`). The matrix says one thing; the org grants another; audit reads the org.

**When it occurs:** After a support push, an acquisition, or a "temporary" grant made while the accountable person was on leave. Delegate groups are rarely reviewed because they are invisible from the objects and permission sets people do review.

**How to avoid:** Treat the delegate group as the deployable expression of the permission row. `DelegateGroup` components carry the suffix `.delegateGroup` in the `delegateGroups` folder and are available in API version 36.0 and later, so they retrieve and diff like any other metadata — and only users with the "View Setup and Configuration" permission can be delegated administrators at all. Retrieve the delegate groups at each phase review, diff them against the matrix, and treat a difference as a decision that was made outside the governance path. See `skills/admin/delegated-administration/SKILL.md` for the design, and `references/worked-examples.md` §6 for the worked artefact.

---

## Gotcha 15: The same role maps to different people in each org

**What happens:** A multi-org programme writes one matrix with one "release manager" column. In practice each org has its own release manager, its own role hierarchy, and its own delegate groups — and the same developer name means different authority in each. A `DelegateGroup` whose `<roles>` element names `Service_EMEA_Manager` grants over whatever that role covers *in the org it is deployed to*; deploy the same file to the second org and it grants over a different population. The matrix reads as agreed while the two orgs behave differently.

**When it occurs:** M&A programmes, regional orgs under one brand, and any org-split where the second org was stood up by a different team. It surfaces at the first cross-org release, when both release managers assume the other one is holding the gate.

**How to avoid:** Scope the column, not just the role: `RM_A` and `RM_B`, each with a named individual and an org. Where one decision genuinely spans orgs — the org strategy itself, the cross-org integration pattern, the master data model — hold **A** at a steering committee rather than at one org's manager, and say so in the escalation path. `agents/multi-org-drift-analyzer/AGENT.md` finds the configuration divergence; the RACI is where you decide who is allowed to resolve it.
