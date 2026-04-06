# Gotchas — Sales Cloud Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Lead Conversion Fires All Object Triggers in One Transaction

**What happens:** When a Lead is converted, the platform creates or updates Account, Contact, and Opportunity records within a single Apex transaction. All before-insert, after-insert, before-update, and after-update triggers on Lead, Account, Contact, and Opportunity fire within the same 150-DML / 100-SOQL governor limit envelope.

**When it occurs:** Any org that has automations on Account, Contact, and Opportunity individually. Each automation is safe in isolation, but combined during lead conversion, the aggregate query and DML counts can exceed limits — especially during bulk lead conversion via Data Loader or API.

**How to avoid:** Profile the governor limit consumption of each object's automation independently, then sum them for the lead conversion scenario. Keep each object's automation under 25% of limits to leave headroom for the combined transaction. Use lazy-loading patterns in triggers (only query when needed) and avoid redundant parent-record queries across child triggers.

---

## Gotcha 2: Roll-Up Summary Field Limit on Account Is 25

**What happens:** Account is limited to 25 roll-up summary fields across all child objects (Opportunity, Contact, Case, custom objects). Architects who design dashboards using roll-up summaries for KPIs (total pipeline, win rate, average deal size, last activity date, open cases) hit this ceiling midway through implementation.

**When it occurs:** Typically during Phase 2 or Phase 3 of a Sales Cloud implementation when reporting requirements expand beyond initial scope. The limit is per-object, not per-child-relationship, so even unused legacy roll-ups count.

**How to avoid:** Audit existing roll-up summary fields before designing new ones. For calculated aggregates that change infrequently (quarterly revenue, lifetime value), use scheduled batch Apex to populate custom fields instead of roll-ups. For real-time aggregates, evaluate Declarative Lookup Rollup Summaries (DLRS) as an open-source alternative that is not subject to the 25-field limit, though it has its own performance considerations.

---

## Gotcha 3: Opportunity Splits Are Deleted When Team Members Are Removed

**What happens:** Removing a user from an Opportunity Team silently deletes all their associated Opportunity Splits. There is no soft-delete or recycle bin recovery for splits. If the splits are used for commission reporting or revenue recognition, the downstream data is permanently lost.

**When it occurs:** During territory realignment when team members are reassigned, during user deactivation workflows, or when admins clean up stale team assignments. Automated processes that modify Opportunity Teams (e.g., territory-based team assignment Flows) can inadvertently trigger this.

**How to avoid:** Before removing team members, snapshot their split data to a custom object (`Split_History__c`). If using automated territory reassignment, add a pre-check step that preserves split records before modifying team membership. Alternatively, use revenue splits with an "Other" team-member placeholder that retains the split allocation when the original user is removed.

---

## Gotcha 4: Forecast Hierarchy Recalculation Lag

**What happens:** When the forecast hierarchy (derived from role hierarchy or territory hierarchy) changes, Salesforce initiates a background recalculation of all forecast rollups. For orgs with 1000+ users and millions of opportunity records, this recalculation can take 4-12 hours. During this window, forecast numbers displayed in Forecast tabs and reports are inconsistent — some rollup to old hierarchy nodes, others to new ones.

**When it occurs:** Any time role assignments change for users who own opportunities, or when territory hierarchy nodes are restructured. It is particularly problematic during quarterly territory realignment when many changes happen simultaneously.

**How to avoid:** Schedule hierarchy changes during weekends or low-activity periods. Batch hierarchy changes rather than making them incrementally over several days (each change restarts the recalculation). Communicate the expected inconsistency window to sales leadership. Consider freezing forecast submissions during the recalculation period.

---

## Gotcha 5: Person Accounts Break Standard Lead Conversion

**What happens:** When Person Accounts are enabled, lead conversion behavior changes significantly. Converting a lead with `IsPersonAccount = true` creates a Person Account (Account without a separate Contact) instead of the standard Account + Contact pair. Field mappings for Person Account fields differ from Business Account mappings. If the architecture assumes standard Account + Contact creation on every conversion, Person Account orgs will have broken post-conversion automations.

**When it occurs:** Orgs that sell to both businesses (B2B) and individuals (B2C) enable Person Accounts. The behavioral difference surfaces during lead conversion and affects every downstream automation that references `Contact` fields created by conversion.

**How to avoid:** If Person Accounts are enabled or planned, design lead conversion automations to handle both paths — Business Account (Account + Contact) and Person Account (Account only). Use `Account.IsPersonAccount` to branch logic. Test lead conversion automations with both record types before go-live.
