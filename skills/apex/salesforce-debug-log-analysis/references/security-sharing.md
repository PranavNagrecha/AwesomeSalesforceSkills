# Security and Sharing in Debug Logs

Salesforce's security model is multi-layered. Debug logs show some security events directly and leave others invisible (by design). This reference covers what you can and cannot determine from a log, and how to diagnose access issues.

## The Salesforce security stack (layers in order)

When a user accesses a record, access is granted only if every layer allows it:

1. **Organization-Wide Defaults (OWD)**: baseline sharing per object (Public Read/Write, Public Read Only, Private).
2. **Role Hierarchy**: users above in the hierarchy see records owned by users below, if "Grant Access Using Hierarchies" is enabled.
3. **Sharing Rules**: criteria-based or ownership-based rules that open access beyond OWD.
4. **Manual Sharing**: record owner shares explicitly via the Share button.
5. **Apex Managed Sharing**: Apex-created entries in `__Share` tables.
6. **Teams**: Account Teams, Opportunity Teams, Case Teams.
7. **Territory Management**: users in territories see records assigned to the territory.
8. **Implicit Sharing**: Account parent sharing to Contacts/Opportunities, and back up.
9. **Group Membership**: users in Public Groups or Queues get shared records.
10. **Restriction Rules (newer)**: filter visible records further; override sharing that would otherwise grant access.

Object-level (CRUD) permissions come from Profile and Permission Sets:
- **Profile**: one per user, baseline.
- **Permission Set**: additive, multiple per user.
- **Permission Set Group**: bundle of permission sets (Summer '20+).

Field-level (FLS) permissions also come from Profile and Permission Sets, per field per object.

## What the log shows about security

Directly visible in logs:
- **Sharing mode entry/exit**: `SYSTEM_MODE_ENTER` and `SYSTEM_MODE_EXIT` when `without sharing` is in effect.
- **Access denial errors**: `INSUFFICIENT_ACCESS_OR_READONLY`, `INSUFFICIENT_ACCESS_ON_CROSS_REFERENCE_ENTITY`.
- **User context**: `USER_INFO` event at the top of the log shows running user, language, locale.
- **Implicit system mode in triggers**: Apex triggers run in system mode by default.
- **FLS enforcement**: `WITH SECURITY_ENFORCED` clauses on SOQL, checked at query time.
- **stripInaccessible**: method calls visible, removing fields the user cannot access.

Not directly visible (have to infer or check outside the log):
- Which specific sharing rule grants or denies access.
- Profile or permission set assignments.
- OWD settings.
- Role hierarchy.
- Territory assignments.
- Criteria-based sharing configurations.
- Implicit sharing calculations.

## The `with sharing` / `without sharing` keywords

Apex classes can be declared:
- `with sharing`: user's record-level sharing is enforced.
- `without sharing`: sharing is NOT enforced; code sees all records it queries.
- `inherited sharing`: inherits from caller. If called directly (not from another Apex class), defaults to `with sharing`.

Log signature for `without sharing`:
```
SYSTEM_MODE_ENTER|without sharing
... code runs ...
SYSTEM_MODE_EXIT
```

### CRUD and FLS are separate from sharing

`with sharing` only affects record-level visibility. It does NOT enforce:
- Object CRUD (can user read/create/edit/delete this type of record)?
- Field-level security (can user see/edit this specific field)?

To enforce CRUD/FLS, you must use:
- `WITH SECURITY_ENFORCED` in SOQL (Spring '20+)
- `Security.stripInaccessible()` method
- Manual `Schema.sObjectType.Contact.fields.Email.isAccessible()` checks

### Enterprise patterns

Most mature orgs have:
- Trigger handler classes in `without sharing` (for integration logic that needs to see all records).
- Business logic classes in `with sharing` (respecting user context).
- DTO/helper classes in `inherited sharing`.

Deviation from this pattern is a code smell. When debugging permission errors, check the sharing mode of every class in the stack.

## SOQL security modes

### WITH SECURITY_ENFORCED (Spring '20+)

```apex
[SELECT Name, Email FROM Contact WITH SECURITY_ENFORCED]
```

The query enforces FLS and CRUD for every field referenced. If the user lacks access to any field, the query throws `System.SecurityException`.

Log signature: when this throws, you see `EXCEPTION_THROWN|System.SecurityException: No access to entity: Contact` or field-specific error.

### USER_MODE and SYSTEM_MODE (Winter '23+)

```apex
[SELECT Name FROM Account WITH USER_MODE]
[SELECT Name FROM Account WITH SYSTEM_MODE]
```

`USER_MODE` enforces sharing, CRUD, and FLS all at once. `SYSTEM_MODE` bypasses all three (requires specific permissions).

Log signature: visible in query text only, not as a distinct event.

### stripInaccessible

```apex
List<Contact> contacts = [SELECT Name, SSN__c FROM Contact];
SObjectAccessDecision dec = Security.stripInaccessible(AccessType.READABLE, contacts);
List<Contact> safeContacts = (List<Contact>) dec.getRecords();
Map<String, Set<String>> removed = dec.getRemovedFields();
```

Fields the user cannot read are removed from the returned list.

Log signature: method call visible, but the field-by-field decisions are not.

## FLS diagnostics

When FLS blocks access:
- `System.SecurityException` with field name.
- Error message names the field and object.

When FLS silently filters (via stripInaccessible):
- No error, but fields are null in returned records.
- Hard to detect from log alone. Check `getRemovedFields()` result if the code exposes it via `USER_DEBUG`.

## Implicit sharing

Salesforce auto-shares records based on relationships. These shares do not have visible log events but affect what users see.

### Account implicit sharing to Contacts and Opportunities

If a user has access to an Account, they can see Contacts and Opportunities on that Account per the parent object's sharing setting (View/Edit).

### Opportunity implicit sharing back to Account

If a user has access to an Opportunity, they get implicit read access to the parent Account.

### Child to parent vs parent to child

- Parent Account to child Opportunity: implicit share based on Opportunity configuration.
- Child Opportunity to parent Account: always Read-only implicit.

These are not visible in logs. They show up only as "user can access the record" without an obvious sharing rule.

## Apex Managed Sharing

Programmatically written sharing records in `__Share` tables (e.g., `AccountShare`, `CustomObject__Share`).

Required fields:
- `ParentId`: the record being shared.
- `UserOrGroupId`: who is receiving access.
- `AccessLevel`: Read, Edit, or All.
- `RowCause`: "Manual" or custom (requires specific Sharing Reason setup).

Inserted as DML:
```
DML_BEGIN|[line]|Op:Insert|Type:AccountShare|Rows:5
```

Visible as normal DML. To identify: filter DML on `*__Share` types.

### Restricting share deletion

Apex-inserted shares with `RowCause = 'Manual'` can be deleted by any user with Modify All Data. Custom RowCause shares require the specific cause to be granted.

## OWD (Organization-Wide Defaults)

The baseline for record-level sharing, per object.

### Options

- **Public Read/Write**: everyone in the org sees and edits.
- **Public Read Only**: everyone sees, only owner and above hierarchy edit.
- **Private**: only owner and above hierarchy see.
- **Controlled by Parent**: sharing comes from the parent (master-detail).

### External vs Internal OWD

Orgs with Experience Cloud users have two OWD columns: Internal (employees) and External (portal/community users). External is typically more restrictive.

### Impact on logs

OWD controls what queries return, not what the log shows. If a user cannot see a record, the query returns zero rows for that record. No log event indicates "record filtered out by OWD".

## Sharing rules

Additive to OWD. Rules can be:
- **Owner-based**: "share records owned by these users with these users".
- **Criteria-based**: "share records matching this criteria with these users".
- **Guest User**: "share records matching criteria with all guest users of community X".

Not visible in logs. To see what rules apply, check Setup > Sharing Settings.

## Role hierarchy

Users above in the hierarchy inherit access to records owned by users below (if "Grant Access Using Hierarchies" is checked).

Not visible in logs. Check Setup > Roles.

## Territory Management

Assigns records to territories; users in a territory see assigned records.

Log signatures:
- DML on `Territory2` and related objects.
- Apex class `Territory2Service` or similar.

## Restriction rules (Winter '22+)

Filter records from certain users even if sharing would otherwise grant access. Inverse of sharing rules.

Not directly visible in logs. If a user unexpectedly cannot see records, check Setup > Object > Restriction Rules.

## Permission Set vs Profile

- Profile: one per user, assigned at user creation.
- Permission Set: additive, zero or many per user.
- Permission Set Group: bundle (Summer '20+).

Salesforce is migrating everything to permission sets. Profiles will eventually be minimal.

Log not directly informative. Check User > Permission Set Assignments.

## Guest User (Experience Cloud / Sites)

Unauthenticated users access community pages as the Guest User for that community.

### Guest User restrictions

- Cannot own records.
- Must have Sharing Rules explicitly granting access.
- No "Update Records You Own" permission.
- Limited object and field access via Profile.

### Common Guest User issues

- Record created by Guest User has `OwnerId` = some default user, causes downstream confusion.
- Guest User cannot see records they just created unless sharing rule matches.
- Guest User profile must grant object CRUD.
- Security review: Guest User should have minimal access.

### Log signature

Running user in `USER_INFO` shows as the Guest User ID, often named "Site Guest User" or similar.

## Shield Platform Encryption

Encrypts data at rest. Fields marked for encryption are stored encrypted in the database.

### Access requirements

- "View Encrypted Data" permission needed to see encrypted values.
- Without it, user sees masked values (e.g., `****` or `Encrypted`).

### Log signatures

Encrypted fields in record dumps show:
- `****` if user lacks View Encrypted Data.
- Actual value if user has it.

### Gotchas

- Formula fields referencing encrypted fields may not be computable.
- SOQL filtering on encrypted fields has restrictions (no case-insensitive search, etc.).
- Encryption keys managed via Setup > Platform Encryption.

## OAuth and Connected App permissions

External systems authenticate via Connected Apps. The app's OAuth scopes determine what the authenticated session can do.

### Log signature

No direct event, but the running user reflects the OAuth context. `UserInfo.getClientAppId()` returns the Connected App ID (not in logs unless explicitly debugged).

### Common issues

- App not pre-authorized: user prompt required, cannot be scripted.
- IP restrictions: Connected App profile restrictions.
- Session trust: "High Assurance" session required for certain objects (Reports, Dashboards).

## Setup audit trail and field history

Not in debug logs but related:
- **Setup Audit Trail** (Setup > View Setup Audit Trail): who changed what config.
- **Field History Tracking**: who changed what field, up to 20 fields per object.

These help diagnose issues that are not visible in real-time logs.

## Security-related grep recipes

```bash
# System mode transitions
grep "SYSTEM_MODE_ENTER\|SYSTEM_MODE_EXIT" log.log

# Access denied errors
grep "INSUFFICIENT_ACCESS\|SecurityException" log.log

# Sharing DML (Apex managed sharing)
grep "DML_BEGIN" log.log | grep "__Share"

# Running user
grep "USER_INFO" log.log

# Encrypted field access (if masked)
grep -E "\*\*\*\*|Encrypted" log.log | head
```

## Common security gotchas in debug logs

1. **`with sharing` class calling `without sharing` class**: the `without sharing` context applies for that call. Sensitive logic inadvertently bypasses sharing.
2. **Trigger on a record the user cannot see**: if the trigger queries other records, it queries in system mode by default, potentially returning records the user cannot see.
3. **LWC @AuraEnabled in `without sharing`**: common pattern but means user's record access is bypassed. Must manually enforce CRUD/FLS.
4. **Community user with profile that grants View All Data**: massive over-privilege. Rare but happens.
5. **Guest User creating records**: ownership is a default user, not the Guest. Sharing may not apply as expected.
6. **Managed package running in `without sharing`**: most packages do, for their integration logic. They have all data access.
7. **`with sharing` combined with `cacheable=true`**: cacheable methods are user-scoped but shared across sessions. Caching decisions need care.

## Debugging access issues: full checklist

When a user reports "I can't see record X":

1. Check object CRUD: Profile/Permission Set > Object Settings > Read.
2. Check FLS for the specific field: Profile/Permission Set > Field-Level Security.
3. Check OWD for the object: is it Public? Private?
4. Check ownership: who owns record X?
5. Check role hierarchy: is the user above the owner in the role hierarchy?
6. Check sharing rules: any rule granting access to this user?
7. Check manual shares: is there a manual share for this record + user?
8. Check implicit sharing: for Contact/Opportunity, does the user have Account access?
9. Check territory assignments (if in use).
10. Check Apex managed sharing entries: any `__Share` records for this record + user?
11. Check restriction rules: is a restriction rule hiding this record from this user?
12. Check Community / Guest User configuration (if relevant).
13. Check Shield Platform Encryption: does the user have View Encrypted Data?
14. Check "High Assurance" session requirements.

If still stuck, use the Login As feature and reproduce in the UI. The UI error messages are typically more specific than log errors.
