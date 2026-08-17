# Examples — Sharing Rules

---

## Example 1: Services Desk Needs Read on Accounts Owned by One Sales Branch

**Context:** An org with roughly 400,000 Account records runs Private OWD on Account. The services desk (14 users, one role, no subordinates) handles onboarding for every deal the West sales branch closes. They cannot see the accounts. The West branch is three roles deep — a manager role with two rep roles beneath it — and reps move between them a few times a year.

**Problem:** The role hierarchy gives the West manager visibility into the reps' accounts, but the services desk sits in a different branch entirely and hierarchy access never travels sideways. Manual sharing was the interim fix; it has produced roughly 200 ad-hoc shares and each one dies the moment an account is transferred, because Salesforce deletes `Manual` row-cause shares on ownership change.

**Solution:**

Step 1 — build the two groups so the rule survives role churn:

```
Setup → Public Groups → New
  Label: West Sales Reps
  Members: Roles and Internal Subordinates → West Sales Manager

Setup → Public Groups → New
  Label: Services Desk
  Members: Role → Services Onboarding
```

Step 2 — retrieve the object's existing rules before adding to them:

```bash
sf project retrieve start -m "SharingOwnerRule:Account.*"
```

Step 3 — add the owner-based rule to `force-app/main/default/sharingRules/Account.sharingRules-meta.xml`:

```xml
<sharingOwnerRules>
    <fullName>West_Reps_To_Services_Desk</fullName>
    <accessLevel>Read</accessLevel>
    <accountSettings>
        <caseAccessLevel>Read</caseAccessLevel>
        <contactAccessLevel>Read</contactAccessLevel>
        <opportunityAccessLevel>None</opportunityAccessLevel>
    </accountSettings>
    <description>Onboarding reads West-owned accounts with cases and contacts. Pipeline deliberately excluded.</description>
    <label>West Reps to Services Desk</label>
    <sharedFrom>
        <group>West_Sales_Reps</group>
    </sharedFrom>
    <sharedTo>
        <group>Services_Desk</group>
    </sharedTo>
</sharingOwnerRules>
```

Step 4 — deploy, then verify against the share table rather than by asking a user:

```soql
SELECT COUNT(Id)
FROM AccountShare
WHERE RowCause = 'Rule'
  AND UserOrGroupId = '00GXX00000ServicesDesk'
```

Run it twice a few minutes apart. A rising count is recalculation in progress.

Step 5 — negative test. Log in as a services desk user and open an account owned by the *East* branch. It must not be visible. A rule that grants more than intended usually shows up here and nowhere else.

**Why it works:** The rule keys on the owner's group membership, so a rep moving between West roles keeps their accounts in scope automatically and a rep leaving West takes theirs out. The `accountSettings` block is the deliberate part: cases and contacts are what onboarding actually needs, so opportunity access is pinned to `None` rather than left at whatever the picker offered. The 200 manual shares can now be deleted — they were the symptom.

**Source:** [T1] Metadata API Developer Guide — SharingRules / SharingBaseRule — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_sharingrules.htm; [T1] Record-Level Access: Under the Hood (manual-share deletion on ownership change).

---

## Example 2: Channel Team Needs Edit on Partner Accounts Regardless of Owner

**Context:** The same org has ~9,000 accounts flagged `Type = 'Partner'`, owned by 60 different reps across every branch. A six-person channel team needs to maintain those accounts and their contacts. Ownership is irrelevant to the requirement and will never be consolidated.

**Problem:** An owner-based rule cannot express this — there is no group of owners, the population is defined by a field. The team currently has `Modify All` on Account from a permission set granted "temporarily" two years ago, which also gives them every non-partner account in the org.

**Solution:**

Criteria-based rule with an explicit `booleanFilter`, because there are two conditions:

```xml
<sharingCriteriaRules>
    <fullName>Partner_Accounts_To_Channel</fullName>
    <accessLevel>Edit</accessLevel>
    <accountSettings>
        <caseAccessLevel>None</caseAccessLevel>
        <contactAccessLevel>Edit</contactAccessLevel>
        <opportunityAccessLevel>None</opportunityAccessLevel>
    </accountSettings>
    <description>Channel team maintains partner accounts and their contacts. No cases, no pipeline.</description>
    <label>Partner Accounts to Channel Team</label>
    <sharedTo>
        <group>Channel_Team</group>
    </sharedTo>
    <booleanFilter>1 AND 2</booleanFilter>
    <criteriaItems>
        <field>Type</field>
        <operation>equals</operation>
        <value>Partner</value>
    </criteriaItems>
    <criteriaItems>
        <field>Active__c</field>
        <operation>equals</operation>
        <value>true</value>
    </criteriaItems>
    <includeRecordsOwnedByAll>true</includeRecordsOwnedByAll>
</sharingCriteriaRules>
```

`includeRecordsOwnedByAll` is `true` here on purpose: several hundred partner accounts are owned by the data-integration user, which has no role, and the requirement is that the channel team can maintain all partner accounts. That decision is permanent — the Metadata API states you can't edit the field after the rule is created.

Then remove the over-broad grant that the rule replaces:

```
Setup → Permission Sets → Channel Ops → Object Settings → Accounts
  Uncheck: Modify All
```

Verify both directions:

```soql
-- The rule is producing grants
SELECT COUNT(Id) FROM AccountShare
WHERE RowCause = 'Rule' AND UserOrGroupId = '00GXX00000ChannelTeam'

-- And the account population is what you expect it to cover
SELECT COUNT(Id) FROM Account WHERE Type = 'Partner' AND Active__c = true
```

**Why it works:** The criteria travel with the record, so a partner account transferred to a new rep stays in scope and a non-partner account never enters it. Dropping `Modify All` in the same change is the point of the exercise — the rule is the narrow version of the access the permission set was granting broadly, and leaving both in place would mean the rule changes nothing while the audit finding remains.

**Source:** [T1] Metadata API Developer Guide — SharingCriteriaRule (`booleanFilter`, `criteriaItems`, `includeRecordsOwnedByAll` write-once) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_sharingrules.htm.

---

## Example 3: Publishing a Catalogue Object to an Experience Cloud Site

**Context:** A custom object `Program__c` holds ~2,000 public course listings. A public Experience Cloud site must render them to unauthenticated visitors. External OWD on `Program__c` is Private.

**Problem:** Guest visitors resolve to the site's guest user, which is not a member of any public group an admin manages in the usual way, and the object is private.

**Solution:**

```xml
<!-- force-app/main/default/sharingRules/Program__c.sharingRules-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<SharingRules xmlns="http://soap.sforce.com/2006/04/metadata">
    <sharingGuestRules>
        <fullName>Published_Programs_To_Site_Guest</fullName>
        <accessLevel>Read</accessLevel>
        <description>Public catalogue listings visible to unauthenticated site visitors.</description>
        <label>Published Programs to Site Guest</label>
        <sharedTo>
            <guestUser>Course_Catalogue_Site</guestUser>
        </sharedTo>
        <criteriaItems>
            <field>Publication_Status__c</field>
            <operation>equals</operation>
            <value>Published</value>
        </criteriaItems>
        <includeHVUOwnedRecords>false</includeHVUOwnedRecords>
    </sharingGuestRules>
</SharingRules>
```

Verify by loading the site in a private browser window with no session, and by confirming that a `Program__c` record in `Draft` status returns a not-found page rather than content.

**Why it works:** `SharingGuestRule` is the supported mechanism for unauthenticated access, and its `accessLevel` is fixed at `Read` — the platform will not let this rule become a write path even by mistake. Criteria on guest rules require API version 48.0 or later, so a project pinned to an older API version has to publish by a different discriminator.

**Source:** [T1] Metadata API Developer Guide — SharingGuestRule (API 47.0+, criteria at 48.0+, `accessLevel` "can be set only to Read") — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_sharingrules.htm.

---

## Anti-Pattern: Deleting Share Rows to Fix an Over-Broad Rule

**What practitioners do:** An audit flags that a criteria-based rule is exposing more records than intended — the criteria were written as `Type equals Partner` when they should also have excluded terminated partners. Rather than fix the rule (which means a recalculation and a change request), someone exports the offending rows from `AccountShare`, filters to the unwanted accounts, and deletes them with Data Loader.

**What goes wrong:** The deletion succeeds. The rows come back. `RowCause = 'Rule'` shares are managed by the platform, and the Apex Developer Guide states that the reason "determines the type of sharing, which controls who can alter the sharing record" — `RowCause` and the parent key are both marked as fields that can't be updated. Any subsequent recalculation touching those accounts — a rep changing role, a group membership edit, an unrelated bulk update to a criteria field — rewrites every grant the rule describes. Meanwhile the audit finding is recorded as remediated, and nobody re-checks it because the evidence at the time of the check was genuine.

**Correct approach:** Change what produces the grant.

1. Amend the criteria so the unwanted records stop matching:

```xml
<booleanFilter>1 AND 2</booleanFilter>
<criteriaItems>
    <field>Type</field>
    <operation>equals</operation>
    <value>Partner</value>
</criteriaItems>
<criteriaItems>
    <field>Partner_Status__c</field>
    <operation>notEqual</operation>
    <value>Terminated</value>
</criteriaItems>
```

2. Deploy and let recalculation delete the grants itself.
3. Confirm with a `RowCause` count that the population shrank, and re-run the audit query after the job settles rather than immediately.

If the requirement is genuinely "subtract access that some other mechanism grants," no sharing rule edit will do it — that is `admin/restriction-rules`. Use the share table to *diagnose* over-sharing and never to remediate it.

**Source:** [T1] Apex Developer Guide — Creating Apex Managed Sharing (share object fields, `RowCause` immutability) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_bulk_sharing_creating_with_apex.htm.
