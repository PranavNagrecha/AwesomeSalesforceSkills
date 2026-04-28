# B2C / Person-Account Matching + Duplicate Rule — Authoring Template

Use this template when authoring a fresh PA-aware match rule + duplicate rule pair.
Replace every `<<...>>` placeholder. The shape encodes the canonical guidance from `SKILL.md`:
build on `Account`, target Person fields, gate with `IsPersonAccount`, normalize phone via `Phone`
matching method, and let lead-convert hit this rule.

---

## 1. Scope

- **Org type:** << B2C-only / mixed B2B+B2C >>
- **Rule purpose:** << e.g. "block duplicate consumer creation on PersonEmail or normalized mobile" >>
- **Lead-convert path:** << Lead → PA / Lead → Account+Contact / N/A >>
- **Volume profile:** << e.g. "5M PA records, ~10k inserts/day" >>

---

## 2. Matching Rule (Account-targeted, PA-aware)

`force-app/main/default/matchingRules/Account.<<RULE_NAME>>.matchingRule-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<MatchingRule xmlns="http://soap.sforce.com/2006/04/metadata" fullName="Account.<<RULE_NAME>>">
    <booleanFilter>(1 OR 2) AND 3<< AND 4 if RT-filter >></booleanFilter>
    <description><<one-line description: "B2C consumer match - PersonEmail OR PersonMobilePhone, gated by IsPersonAccount.">> </description>
    <label><<Human-readable label, e.g. "B2C Consumer Match">></label>
    <ruleStatus>Active</ruleStatus>

    <!-- 1. Email - case-insensitive by default for Email-typed fields. Do NOT wrap with LOWER(). -->
    <matchingRuleItems>
        <fieldName>PersonEmail</fieldName>
        <matchingMethod>Exact</matchingMethod>
    </matchingRuleItems>

    <!-- 2. Mobile phone - 'Phone' method strips formatting and country-code variants. -->
    <matchingRuleItems>
        <fieldName>PersonMobilePhone</fieldName>
        <matchingMethod>Phone</matchingMethod>
    </matchingRuleItems>

    <!-- 3. PA gate - load-bearing in mixed orgs; harmless on B2C-only orgs. -->
    <matchingRuleItems>
        <fieldName>IsPersonAccount</fieldName>
        <matchingMethod>Exact</matchingMethod>
    </matchingRuleItems>

    <!-- 4. Optional record-type gate when multiple PA record types exist (e.g. Customer vs Prospect PA). -->
    <!--
    <matchingRuleItems>
        <fieldName>RecordType.DeveloperName</fieldName>
        <matchingMethod>Exact</matchingMethod>
    </matchingRuleItems>
    -->
</MatchingRule>
```

### Fuzzy variant (name + postal code, when email/phone are missing)

Add these AFTER the email/phone primary match so the rule has both a high-cardinality
path and a fuzzy fallback:

```xml
<matchingRuleItems>
    <fieldName>FirstName</fieldName>
    <matchingMethod>FuzzyFirstName</matchingMethod>
</matchingRuleItems>
<matchingRuleItems>
    <fieldName>LastName</fieldName>
    <matchingMethod>FuzzyLastName</matchingMethod>
</matchingRuleItems>
<matchingRuleItems>
    <fieldName>BillingPostalCode</fieldName>
    <matchingMethod>Exact</matchingMethod>
</matchingRuleItems>
```

Boolean filter pattern: `((1 OR 2) OR (3 AND 4 AND 5)) AND <PA_GATE_INDEX>`.

---

## 3. Duplicate Rule

`force-app/main/default/objects/Account/duplicateRules/Account.<<RULE_NAME>>_Dedupe.duplicateRule-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<DuplicateRule xmlns="http://soap.sforce.com/2006/04/metadata" fullName="<<RULE_NAME>>_Dedupe">
    <actionOnInsert>Block</actionOnInsert>          <!-- B2C consumer dedupe: Block on insert is the safe default. -->
    <actionOnUpdate>Allow</actionOnUpdate>           <!-- Self-match on update should not block reps. -->
    <alertText>A Person Account with this email or mobile phone already exists. Search before creating a new record.</alertText>
    <description><<one-line description>></description>

    <duplicateRuleMatchingRules>
        <matchingRule>Account.<<RULE_NAME>></matchingRule>
        <objectName>Account</objectName>
    </duplicateRuleMatchingRules>

    <!-- Optional: cross-object match against Lead so lead-convert is gated pre-convert. -->
    <!--
    <duplicateRuleMatchingRules>
        <matchingRule>Lead.<<LEAD_RULE_NAME>></matchingRule>
        <objectName>Lead</objectName>
    </duplicateRuleMatchingRules>
    -->

    <isActive>true</isActive>
    <name><<Human-readable name>></name>
    <operationsOnInsert>
        <allowSave>false</allowSave>
        <alertEnabled>true</alertEnabled>
        <reportEnabled>true</reportEnabled>
    </operationsOnInsert>
    <operationsOnUpdate>
        <allowSave>true</allowSave>
        <alertEnabled>true</alertEnabled>
        <reportEnabled>true</reportEnabled>
    </operationsOnUpdate>
    <securityOption>EnforceSharingRules</securityOption>
</DuplicateRule>
```

---

## 4. Mixed-Org Companion: B2B Rule (gated by `IsPersonAccount = false`)

When the org is mixed, also author the parallel B2B rule so the two universes never cross:

```xml
<MatchingRule fullName="Account.<<B2B_RULE_NAME>>">
    <booleanFilter>1 AND 2 AND 3</booleanFilter>
    <label><<B2B label>></label>
    <ruleStatus>Active</ruleStatus>
    <matchingRuleItems>
        <fieldName>Name</fieldName>
        <matchingMethod>FuzzyCompanyName</matchingMethod>
    </matchingRuleItems>
    <matchingRuleItems>
        <fieldName>BillingStreet</fieldName>
        <matchingMethod>FuzzyStreet</matchingMethod>
    </matchingRuleItems>
    <matchingRuleItems>
        <fieldName>IsPersonAccount</fieldName>
        <matchingMethod>Exact</matchingMethod>
    </matchingRuleItems>
</MatchingRule>
```

The B2B Duplicate Rule's match formula adds `AND IsPersonAccount = FALSE`; the B2C side adds
`AND IsPersonAccount = TRUE`. They are mutually exclusive.

---

## 5. Pre-deploy Checks

- [ ] Account-targeted matching rule references `PersonEmail` / Person* phone fields, NOT `Contact.*`
- [ ] `IsPersonAccount` match item present in every PA-targeted rule
- [ ] Phone fields use `matchingMethod = Phone`, not `Exact`
- [ ] No `LOWER(...)` wrapper on the email match field
- [ ] Fuzzy-name uses `FuzzyFirstName` / `FuzzyLastName`, not `FuzzyCompanyName` on `Account.Name`
- [ ] Lead-convert path: at least one Account-targeted Duplicate Rule is active
- [ ] In mixed orgs: parallel B2B + B2C rules with mutually exclusive `IsPersonAccount` gates
- [ ] `python3 scripts/check_duplicate_rule_person_account_edge_cases.py force-app/main/default` exits 0

---

## 6. Field-reference cheat sheet (Account-side PA fields)

| Concern | Field on Account | Notes |
|---|---|---|
| Email | `PersonEmail` | Email type, case-insensitive on `Exact` match |
| Mobile | `PersonMobilePhone` | Use `matchingMethod = Phone` |
| Home phone | `PersonHomePhone` | Same |
| Primary phone | `Phone` | Same; on PA this is the "best" phone, often duplicates Mobile |
| Other phone | `OtherPhone` | Same |
| Person flag | `IsPersonAccount` | The required gate |
| Person record type | `RecordType.IsPersonType` (read) / `RecordTypeId` (filter) | Use when multiple PA RTs exist |
| First name | `FirstName` | Person-side only; null on B2B |
| Last name | `LastName` | Person-side only; null on B2B |
| Postal code | `BillingPostalCode` | Address fields are shared with B2B; gate with `IsPersonAccount` |
