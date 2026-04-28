# Examples — Duplicate Rule Person Account Edge Cases

Three realistic scenarios showing PA-specific match-rule design (and how it fails when the B2B mental model leaks in).

---

## Example 1 — PA email mismatch: PersonEmail vs Contact.Email

### Scenario

A B2C retailer enables Person Accounts and ports its B2B duplicate rule onto the Account object. The rule references `Contact.Email` as the match field because "the Person Contact has the email." Deployment fails with:

```text
INVALID_FIELD: Contact.Email is not a valid field on Account
```

The team "fixes" this by rebuilding the rule on the Contact object and matching `Email`. Deploy succeeds. But two weeks later, reps in the Account list view start creating duplicate Person Accounts with the same email — the dedupe alert never fires.

### Root cause

A Matching Rule fires on the SObject it is built on. The Contact-targeted rule never evaluates when a user clicks "New Person Account" on the Account list view (which writes to the Account side first; the Person Contact row is created by the platform after the Account save succeeds). Lead convert that lands on PA also runs the Account-targeted rule, not the Contact one.

### Correct rule

Build the matching rule on `Account`, reference `PersonEmail`, gate with `IsPersonAccount`:

```xml
<MatchingRule fullName="Account.B2C_Email_Match">
    <booleanFilter>1 AND 2</booleanFilter>
    <description>PA email match - case-insensitive on PersonEmail.</description>
    <label>B2C Email Match</label>
    <matchingRuleItems>
        <fieldName>PersonEmail</fieldName>
        <matchingMethod>Exact</matchingMethod>
    </matchingRuleItems>
    <matchingRuleItems>
        <fieldName>IsPersonAccount</fieldName>
        <matchingMethod>Exact</matchingMethod>
    </matchingRuleItems>
</MatchingRule>
```

```xml
<DuplicateRule fullName="Account.B2C_Email_Dedupe">
    <actionOnInsert>Block</actionOnInsert>
    <actionOnUpdate>Allow</actionOnUpdate>
    <alertText>A Person Account with this email already exists.</alertText>
    <duplicateRuleMatchingRules>
        <matchingRule>Account.B2C_Email_Match</matchingRule>
        <objectName>Account</objectName>
    </duplicateRuleMatchingRules>
    <isActive>true</isActive>
    <name>B2C Email Dedupe</name>
</DuplicateRule>
```

### Why it works

- `PersonEmail` is the canonical Account-side person email field — it is what the Account UI writes to.
- The `Exact` method on an Email-type field is case-insensitive by Salesforce default (`a@x.com` matches `A@X.COM`); no `LOWER()` wrapper needed.
- The `IsPersonAccount` clause prevents matching against future B2B records.

---

## Example 2 — Lead-to-PA convert duplicate not blocked

### Scenario

A consumer-finance org runs a webform-to-Lead pipeline. Each Lead converts (via a Flow) into a Person Account. They have an active **Lead-targeted** Duplicate Rule that catches duplicate Leads pre-convert. They expect convert to also block when the resulting PA collides with an existing one. It does not. Reps start seeing two Person Accounts for "Jamie Rivera" with the same email.

### Root cause

Lead-convert is an insert against the **target** SObject. When the target is a Person Account, the platform inserts into Account, and any Account-targeted Duplicate Rule fires. The Lead-targeted rule did its job (no duplicate Lead survived) — but there was no Account-side rule to catch the collision after convert.

### Correct wiring

Two duplicate rules, both active:

1. **Lead-targeted** rule on `Lead` — catches dup Leads in the inbox before convert.
2. **Account-targeted** rule on `Account`, PA-aware (Pattern A from `SKILL.md`) — fires on the convert-time insert.

```xml
<!-- Lead/duplicateRules/Lead.Convert_Time_Email.duplicateRule-meta.xml -->
<DuplicateRule fullName="Lead.Convert_Time_Email">
    <actionOnInsert>Block</actionOnInsert>
    <actionOnUpdate>Allow</actionOnUpdate>
    <alertText>Lead with this email already exists - merge before converting.</alertText>
    <duplicateRuleMatchingRules>
        <matchingRule>Lead.Email_Match</matchingRule>
        <objectName>Lead</objectName>
    </duplicateRuleMatchingRules>
    <duplicateRuleMatchingRules>
        <matchingRule>Account.B2C_Email_Match</matchingRule>
        <objectName>Account</objectName>
    </duplicateRuleMatchingRules>
    <isActive>true</isActive>
    <name>Lead Convert-Time Email</name>
</DuplicateRule>
```

Cross-object matching (`Lead.Email` ↔ `Account.PersonEmail`) is supported on Lead duplicate rules and is the cleanest way to surface the PA collision *before* the Lead is converted, rather than letting convert produce the dup and rely on a downstream Account-side rule to catch it (which still works but is later in the funnel).

### Why it works

- The Lead-targeted rule with cross-object matching evaluates the Lead's email against existing PAs at the moment of save / convert.
- The Account-targeted rule from Example 1 is a backstop for any direct Account inserts that bypass the Lead path.

---

## Example 3 — B2B match rule reused on B2C, broken silently

### Scenario

A growing org adds Person Accounts on top of an existing B2B Salesforce instance. A senior admin clones the B2B "Account Name + Billing Street" matching rule, renames it `B2C_Match`, points the Duplicate Rule at it, and ships. No deployment errors. Two weeks later:

- Acme Corporation (B2B) is reported as a duplicate of Acme Smith (PA) because both have `Name = "Acme Smith"` after PA name composition.
- Real PA dupes (same `PersonEmail`, slightly different `Name`) are missed entirely.

### Root cause

The B2B rule:

```xml
<MatchingRule fullName="Account.B2B_Match_Cloned">
    <booleanFilter>1 AND 2</booleanFilter>
    <matchingRuleItems>
        <fieldName>Name</fieldName>
        <matchingMethod>Fuzzy:CompanyName</matchingMethod>
    </matchingRuleItems>
    <matchingRuleItems>
        <fieldName>BillingStreet</fieldName>
        <matchingMethod>Fuzzy:Street</matchingMethod>
    </matchingRuleItems>
</MatchingRule>
```

Three problems:

1. No `IsPersonAccount` filter — B2B records compete with B2C records for matches.
2. `Fuzzy:CompanyName` is tuned for legal-entity tokens (Inc, LLC, Co); on a person name it produces low-quality matches.
3. The B2C signal that would actually catch dups (`PersonEmail`, `PersonMobilePhone`) is not in the rule at all.

### Correct rule (parallel B2B + B2C, each gated)

Two matching rules and two duplicate rules:

```xml
<!-- B2B side -->
<MatchingRule fullName="Account.B2B_Match">
    <booleanFilter>1 AND 2 AND 3</booleanFilter>
    <matchingRuleItems>
        <fieldName>Name</fieldName>
        <matchingMethod>Fuzzy:CompanyName</matchingMethod>
    </matchingRuleItems>
    <matchingRuleItems>
        <fieldName>BillingStreet</fieldName>
        <matchingMethod>Fuzzy:Street</matchingMethod>
    </matchingRuleItems>
    <matchingRuleItems>
        <fieldName>IsPersonAccount</fieldName>
        <matchingMethod>Exact</matchingMethod>
    </matchingRuleItems>
</MatchingRule>

<!-- B2C side -->
<MatchingRule fullName="Account.B2C_Match">
    <booleanFilter>(1 OR 2) AND 3</booleanFilter>
    <matchingRuleItems>
        <fieldName>PersonEmail</fieldName>
        <matchingMethod>Exact</matchingMethod>
    </matchingRuleItems>
    <matchingRuleItems>
        <fieldName>PersonMobilePhone</fieldName>
        <matchingMethod>Phone</matchingMethod>
    </matchingRuleItems>
    <matchingRuleItems>
        <fieldName>IsPersonAccount</fieldName>
        <matchingMethod>Exact</matchingMethod>
    </matchingRuleItems>
</MatchingRule>
```

The B2B Duplicate Rule's match formula adds `AND IsPersonAccount = FALSE`; the B2C side adds `AND IsPersonAccount = TRUE`. They are mutually exclusive — no record is ever evaluated by both.

### Why it works

- Each rule looks only at its own universe; B2B fuzzy never crosses into B2C and vice versa.
- The B2C rule uses Person fields that actually carry the consumer signal.
- Adding a future record type (e.g. household) is one more parallel rule, not a rewrite.

---

## Anti-Pattern: matching on FirstName alone in high-volume consumer data

**What practitioners do:** add a "Fuzzy First Name" match item by itself on a B2C org because "we want to catch typos in the same household."

**What goes wrong:** every "Maria" in a 5M-record consumer database matches every other Maria. The duplicate-job runs hit the row-pair limit; reps drown in false positives; real dupes are lost in the noise.

**Correct approach:** never match on `FirstName` alone. Always pair it with at least one high-cardinality field — `PersonEmail` (Exact) or normalized `PersonMobilePhone` (Phone) — and let `LastName` + `BillingPostalCode` serve as a *fuzzy* layer for the email-missing case. High-cardinality first, fuzzy second.
