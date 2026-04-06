# Gotchas — Territory Data Alignment

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Rule Reruns Silently Rebuild Deleted Rule-Driven Associations

**What happens:** An `ObjectTerritory2Association` row with `AssociationCause = 'Territory'` is deleted via API or Data Loader to remove an account from a territory. The deletion succeeds. On the next ETM assignment rule run (manual or triggered by account edit), the row is re-created because the account's field values still satisfy the territory's rule criteria. The account reappears in the territory with no error or notification.

**When it occurs:** Any time you directly delete a rule-driven association without also modifying the underlying rule or account field values. This is most common during quick "hot fix" cleanups when a sales manager asks for an account to be moved immediately before the next rule run.

**How to avoid:** Always check `AssociationCause` before deleting. For `AssociationCause = 'Territory'` rows, the correct action is to change the rule criteria or update the account field that drives the assignment, not to delete the row. If immediate reassignment is needed, delete the rule-driven row AND insert a new `AssociationCause = 'Manual'` row for the correct territory — the manual row will survive rule reruns.

---

## Gotcha 2: Bulk Inserts Do Not Prevent Duplicate ObjectTerritory2Association Rows

**What happens:** The API accepts duplicate inserts for `ObjectTerritory2Association` — the same (ObjectId, Territory2Id) pair can be inserted multiple times, creating multiple rows. This inflates per-territory account counts, causes unexpected behavior in territory-based reports, and leaves orphan rows that are difficult to clean up at scale.

**When it occurs:** During bulk loads when the source data has not been deduplicated against existing associations. Also occurs when a migration script is run more than once without idempotency checks. The duplicate rows are valid from the platform's perspective — there is no unique constraint enforced at the database level on this junction object.

**How to avoid:** Before any bulk insert, query existing `ObjectTerritory2Association` rows for the target model and filter them out of the insert payload. Use an external set comparison (Python, Excel, or SOQL `NOT IN`) to identify net-new rows only. For large-scale migrations, implement idempotency by checking for the presence of each (ObjectId, Territory2Id) pair before inserting.

---

## Gotcha 3: Track Territory Assignment History Does Not Backfill Historical Events

**What happens:** The Track Territory Assignment History feature is enabled in Setup, and the team expects to see a full history of who assigned each account to its territory over time. But the history records only start from the enablement date — all prior assignment events (including the initial bulk load that populated the model) are absent from the history tables.

**When it occurs:** When teams enable the feature after the territory model has already been populated and running for weeks or months, then try to use history records to investigate a pre-enablement assignment or audit a specific account's assignment timeline.

**How to avoid:** Enable Track Territory Assignment History at the same time the territory model is activated — ideally as part of the go-live checklist. If you need a pre-enablement snapshot, export `ObjectTerritory2Association` to an external system before enabling the feature and treat that export as the baseline. For compliance or audit requirements, document the feature enablement date so stakeholders understand the history coverage window.

---

## Gotcha 4: Writing Associations to a Non-Active Model Returns an Opaque Error

**What happens:** An API insert into `ObjectTerritory2Association` fails with a generic error when the target `Territory2Id` belongs to a model in Planning or Archived state. The error message does not clearly state that the model state is the cause, which sends practitioners down a debugging path around field values, permissions, or data types.

**When it occurs:** When a migration or load script references `Territory2Id` values from a Planning model that has not yet been activated, or from an Archived model that was deactivated after the script was prepared. Also occurs when two territory models are in flux simultaneously and the script was prepared against the wrong model.

**How to avoid:** Always query `Territory2Model` to confirm `State = 'Active'` immediately before any write operation, rather than relying on a cached model ID. Add an explicit pre-flight check in migration scripts: `SELECT Id, State FROM Territory2Model WHERE Id = :targetModelId` and assert the result is `Active` before proceeding.

---

## Gotcha 5: UserTerritory2Association Rows Are Not Cleaned Up When a User Is Deactivated

**What happens:** A rep leaves the company and their Salesforce user is deactivated. Their `UserTerritory2Association` rows remain intact. The inactive user still appears as a territory member in territory reports, inflates headcount-per-territory metrics, and their forecast rows may remain in the territory forecast view until the forecast is manually cleaned up.

**When it occurs:** Any user deactivation where the admin does not explicitly delete the corresponding `UserTerritory2Association` rows. This is a silent data quality issue that accumulates over time, particularly in orgs with high rep turnover.

**How to avoid:** Add a user offboarding step to the HR/Salesforce admin process: query `UserTerritory2Association WHERE UserId = :deactivatedUserId AND IsActive = true`, delete those rows, and then transfer any open opportunities previously owned by that user. A quarterly audit query of `UserTerritory2Association` filtered on `User.IsActive = false` can surface accumulated stale rows for bulk cleanup.
