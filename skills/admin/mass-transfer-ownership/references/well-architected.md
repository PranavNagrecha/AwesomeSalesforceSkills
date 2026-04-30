# Well-Architected Notes — Mass Transfer Ownership

## Relevant Pillars

- **Reliability** — A botched mass transfer can corrupt downstream sharing for tens of thousands of records and require hours of recovery. The primary reliability lever is sequencing: transfer before deactivation, defer sharing recalc above ~100k records, and capture rollback CSVs before mutating anything.
- **Operational Excellence** — Mass transfers happen during territory cuts, M&A integration, or quarterly realignment, often under deadline pressure. Standardizing the runbook (inventory → tool → cascade policy → notification policy → execute → validate) turns a stressful event into a predictable one.

## Architectural Tradeoffs

- **Mass Transfer Records vs. Data Loader vs. Apex:** the UI tool is fastest for parent-with-cascade but breaks down beyond standard objects and modest volumes. Data Loader is the workhorse for any object but requires explicit child-object passes. Apex is the only path when you need conditional remap logic, deferred recalc coordination, or trigger suppression.
- **Cascade vs. independent ownership:** cascading children matches user mental models ("the account moved, of course the cases moved") but obscures audit. Independent ownership is more granular but harder to reason about. Document the choice in the territory plan, not just the runbook.
- **Notifications on or off:** turning email notifications off speeds the run and avoids spamming managers with 5,000 emails, but suppresses signal that something moved. For territory cuts, off is usually right; for terminations, often on.

## Anti-Patterns

1. **Deactivating a user before transferring records** — Salesforce blocks the deactivation, but the admin's recovery (reactivate, transfer, deactivate) emits change tracking noise and any password-expiration windows reset. Transfer first.
2. **Treating sharing recalc as instantaneous** — A 200k-record transfer may take an hour for the recalc to settle; a help-desk ticket from a user who can't see "their" record at 9am on Monday is the recalc still running. Schedule transfers in evening windows and communicate the recalc lag.
3. **No rollback CSV** — Without `Id, OldOwnerId, NewOwnerId` saved, undoing a transfer means re-querying owners from history (often unavailable) or guessing.

## Official Sources Used

- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Mass Transfer Records help — https://help.salesforce.com/s/articleView?id=sf.admin_transfer.htm&type=5
- Defer Sharing Calculations help — https://help.salesforce.com/s/articleView?id=sf.security_sharing_defer_sharing_calc.htm&type=5
