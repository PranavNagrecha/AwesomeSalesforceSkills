# Gotchas — Community User Data Migration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: User Insert Fails Without a Valid ContactId on Every Row

**What happens:** Data Loader bulk User insert returns `INVALID_CROSS_REFERENCE_KEY` or `FIELD_INTEGRITY_EXCEPTION: Contact: id value of incorrect type` for every row where ContactId is missing, null, or points to a non-existent Contact record. There is no platform-side fallback — Salesforce does not auto-create Contacts for external users.

**When it occurs:** Any time a User insert CSV is prepared without pre-staging the Contact/Account hierarchy first. Common triggers: migrating from a source system where the Contact relationship is implicit (e.g., the portal user IS the contact record in the old system), or using sandbox-exported ContactIds in a production insert job where those Ids do not exist.

**How to avoid:** Before building the User CSV, run a SOQL query to confirm every source record maps to an existing Contact in the destination org. Use an External ID field on Contact for the join rather than relying on Salesforce record IDs, which differ between environments. Never start a User insert job until the Contact pre-staging job has a confirmed success count matching the source row count.

---

## Gotcha 2: NetworkMember Records Are Not Auto-Cleaned When Profile Changes

**What happens:** When a User's `ProfileId` is updated to a Profile associated with a different Experience Cloud network, Salesforce creates a new `NetworkMember` record for the new network but does not delete the `NetworkMember` record for the old network. The user remains a member of both sites.

**When it occurs:** Any license migration scenario (Customer Community → Customer Community Plus, for example) where the Profile is updated via Data Loader or Apex. Also occurs when a user's profile is reassigned manually in Setup.

**How to avoid:** After any Profile bulk-update, query `NetworkMember` filtered by the old `NetworkId` and the set of updated User IDs. Delete all stale records. Include this as an explicit post-migration step in the runbook — it will not happen automatically. Failing to clean these records can leave users with access to the old site on the lower-privilege license, creating a security exposure.

---

## Gotcha 3: Deactivated Users Still Occupy License Seats During the Migration Window

**What happens:** Deactivating a User record does not immediately release the Experience Cloud license seat. The platform recalculates license consumption on a background schedule, not in real time. If the migration plan relies on freeing old license seats before inserting new users in the same window, the insert will fail with a license limit error even though the old users appear deactivated.

**When it occurs:** In-org license migration where the org is at or near its license limit and the plan calls for deactivating the old cohort and immediately activating the new cohort.

**How to avoid:** Build a buffer into the migration window. Do not plan to free seats and immediately fill them in the same job. If the org is license-constrained, contact Salesforce Support to confirm the seat recalculation cadence for your org, or request a temporary license increase for the migration window.

---

## Gotcha 4: UserType Is Immutable After User Creation

**What happens:** Attempting to update the `UserType` field on an existing User record — via Apex, Data Loader, or the REST API — throws `FIELD_INTEGRITY_EXCEPTION`. The field is set at creation time based on the Profile and cannot be changed directly.

**When it occurs:** Teams attempting to "upgrade" a user's license by changing UserType rather than by reassigning the Profile. Also occurs when migration documentation from older Salesforce releases references UserType as an updatable field.

**How to avoid:** Always perform license migration by updating `ProfileId` to a Profile associated with the destination license type. Never include `UserType` in an update operation CSV. The correct UserType will reflect automatically once the Profile drives the correct license.

---

## Gotcha 5: Sandbox Username Collision Blocks Migration Testing

**What happens:** When a Salesforce sandbox is refreshed, Salesforce appends a suffix to all usernames (e.g., `user@example.com.dev1`). If a team exports User data from the sandbox and attempts to re-insert it into another sandbox or into production without adjusting the `Username` field, every row fails with `DUPLICATE_USERNAME` or `USERNAME_ALREADY_EXISTS`.

**When it occurs:** Any migration test performed by exporting Users from a sandbox and reimporting them into a different environment. Commonly affects teams who use sandbox data as their source-of-truth for the migration CSV.

**How to avoid:** Always scrub the `Username` field in any CSV exported from a sandbox before using it as a migration source. Apply a deterministic transformation (e.g., replace `.dev1` suffix with `.prod` or strip sandbox suffixes entirely) and validate uniqueness with a SOQL query against the target org before submitting the insert job.
