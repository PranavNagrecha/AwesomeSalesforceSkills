# Well-Architected Notes — Mass Transfer Ownership

## Relevant Pillars

- **Reliability** — A botched mass transfer can corrupt downstream sharing for tens of thousands of records and require hours of recovery. The primary reliability lever is sequencing: transfer before deactivation, defer sharing recalc above ~100k records, and capture rollback CSVs before mutating anything.
- **Operational Excellence** — Mass transfers happen during territory cuts, M&A integration, or quarterly realignment, often under deadline pressure. Standardizing the runbook (inventory → tool → cascade policy → notification policy → execute → validate) turns a stressful event into a predictable one.

## Architectural Tradeoffs

- **Mass Transfer Records vs. Data Loader vs. Apex:** the UI tool is fastest for parent-with-cascade but breaks down beyond standard objects and modest volumes. Data Loader is the workhorse for any object but requires explicit child-object passes. Apex is the only path when you need conditional remap logic, deferred recalc coordination, or trigger suppression.
- **Cascade vs. independent ownership:** cascading children matches user mental models ("the account moved, of course the cases moved") but obscures audit. Independent ownership is more granular but harder to reason about. Document the choice in the territory plan, not just the runbook.
- **Notifications on or off:** turning email notifications off speeds the run and avoids spamming managers with 5,000 emails, but suppresses signal that something moved. For territory cuts, off is usually right; for terminations, often on.

- **API speed vs. UI control:** the API path is the only one that scales, but it hands you a
  fixed outcome on two side effects. On Opportunity, the previous owner's access falls to Read
  Only or the org-wide default, whichever is greater, and previous team members stay on the
  team; the user interface instead lets you choose the previous owner's access level when they
  are on the opportunity team. On the new-owner email, the API sends nothing unless the write
  runs through Apex with `Database.DMLOptions.EmailHeader.triggerUserEmail = true`. Choosing
  Bulk API is therefore also choosing "no notification and no access-level choice" — decide
  that deliberately rather than discovering it in the post-mortem.
- **Deferring sharing recalculation vs. living with it:** deferral is a `SharingSettings`
  deploy, but the feature is off until Salesforce Customer Support enables it, and resuming is
  the expensive half — flipping the flags back to false triggers the recalculation you
  postponed. The tradeoff is not "fast vs. slow", it is "one long unpredictable window during
  business hours" vs. "a short write now and a scheduled recalculation you control".

## Anti-Patterns

1. **Deactivating a user before transferring records** — Salesforce blocks the deactivation, but the admin's recovery (reactivate, transfer, deactivate) emits change tracking noise and any password-expiration windows reset. Transfer first.
2. **Treating sharing recalc as instantaneous** — A 200k-record transfer may take an hour for the recalc to settle; a help-desk ticket from a user who can't see "their" record at 9am on Monday is the recalc still running. Schedule transfers in evening windows and communicate the recalc lag.
3. **No rollback CSV** — Without `Id, OldOwnerId, NewOwnerId` saved, undoing a transfer means re-querying owners from history (often unavailable) or guessing.

## Official Sources Used

- Object Reference (v62) — `Account.OwnerId` field table: Refers To **User** only; "For API
  version 12.0 and later, sharing records are kept"; "For API version 16.0 and later, users
  must have the 'Transfer Record' permission in order to update (transfer) account ownership"
  (grounds the queue-vs-user gotcha and the permission gotcha).
  https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_account.htm
- Object Reference (v62) — `Opportunity.OwnerId` and `OpportunityTeamMember` usage note: the
  previous owner's access becomes "Read Only or the access specified in your organization-wide
  default for opportunities, whichever is greater", team members are kept from API version
  12.0, and the UI lets you pick the previous owner's access level (grounds Gotcha 7 and the
  API-vs-UI tradeoff above).
  https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_opportunityteammember.htm
- Object Reference (v62) — `AccountTeamMember` usage note: members added by a user with
  group-based access "are removed after an account's owner is changed … even if the Keep
  account team option is selected" (grounds Gotcha 6 and the team snapshot step).
  https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_accountteammember.htm
- Object Reference (v62) — `UserRecordAccess` (`HasTransferAccess`, 200-id query cap, no
  restriction-rule awareness), `Group.Type = Queue`, `AccountShare.RowCause` values including
  the read-only `Owner` cause, and the Insufficient Access event type's note that bulk-operation
  access errors "aren't logged" (grounds the pre-flight and verification query sets and
  Gotcha 8).
  https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_userrecordaccess.htm
- Metadata API Developer Guide (v62) — `SharingSettings`: `deferGroupMembership` and
  `deferSharingRules` (API 49.0+), "The defer sharing calculation feature isn't enabled by
  default. To enable it for your Salesforce org, contact Salesforce Customer Support", the
  flag-ordering constraint, and the Manage Sharing permission (grounds the deferral artefact
  and Gotcha 13).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Apex Developer Guide (v62) — Triggers and Order of Execution, steps 3–19, including
  assignment rules at step 9 and Criteria Based Sharing evaluation at step 18; Batch Apex
  limits (default scope 200, `QueryLocator` scope max 2,000, 50 million record ceiling)
  (grounds Gotcha 12 and the batch-sizing guidance).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Apex Reference Guide (v62) — `Database.DMLOptions`: `optAllOrNone` semantics,
  `EmailHeader.triggerUserEmail` ("If you use the API to change record ownership … no email
  notification is sent"), and "The `Database.DMLOptions` object supports assignment rules for
  cases and leads, but not for accounts" (grounds the Batch Apex artefact and Gotcha 9).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/apexref.pdf
- Data Loader Guide (v62) — Settings *Assignment rule* field ("The assignment rule overrides
  Owner values in your CSV file"), *Keep Account Teams* (`sfdc.useBulkApi=false`,
  `process.keepAccountTeam=true`, Data Loader 56.0.3+, uniform old/new owner requirement), and
  the `process-conf.xml` / `process.bat` batch-mode contract (grounds Gotchas 9 and 10 and the
  `process-conf.xml` artefact).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_data_loader.pdf
- Bulk API 2.0 Developer Guide (v62) — *Create a Job* request body (`assignmentRuleId`,
  `columnDelimiter`, `contentType`, `externalIdFieldName`, `lineEnding`, `object`,
  `operation`), the single-object-per-job rule, and automatic batching every 10,000 records
  (grounds the Bulk API artefact and the "no owner email on this path" conclusion).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_asynch.pdf
- Salesforce Developer Limits and Allocations Quick Reference (v62) — Bulk API and Bulk API 2.0
  limits: 15,000 batches per rolling 24 hours shared across both APIs, 150,000,000 records per
  24 hours, 150 MB per job (upload ≤100 MB for base64 expansion), 7-day results lifespan, and
  the >2,000-record threshold for choosing Bulk (grounds the allocation table and Gotcha 14).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf
- Salesforce Well-Architected — Reliability and Operational Excellence framing for the pillar
  notes above.
  https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
