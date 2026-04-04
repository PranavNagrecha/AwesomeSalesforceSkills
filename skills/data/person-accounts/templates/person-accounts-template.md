# Person Accounts — Work Template

Use this template when working on Person Account enablement, data model design, migration, or integration tasks.

## Scope

**Skill:** `person-accounts`

**Request summary:** (fill in what the user asked for)

**Work type:** (check one)
- [ ] New enablement (Person Accounts not yet enabled)
- [ ] Post-enablement configuration / data model design
- [ ] Migration from existing Contact-only or Business Account+Contact model
- [ ] Integration update (existing integration needs Person Account awareness)
- [ ] Apex / automation update (existing code needs IsPersonAccount handling)
- [ ] Reporting update (existing reports need Person Account filters)
- [ ] Troubleshooting an existing Person Account issue

---

## Context Gathered

### Org State

- Person Accounts enabled? (yes / no / unknown):
- Org edition:
- Salesforce version / release:
- Approximate Account record volume:
- Approximate Contact record volume:
- Private Contacts (Contacts with null AccountId) — count: (run `SELECT COUNT() FROM Contact WHERE AccountId = null`)

### Org Model

- [ ] Pure B2C (all accounts represent individual people)
- [ ] Pure B2B (all accounts represent organizations)
- [ ] Mixed B2B + B2C

### Person Account Record Types

- Name of Person Account Record Type(s):
- Name of Business Account Record Type(s) (if mixed org):

### Integration Systems

| System | Direction | Object Used | Person Account Aware? |
|--------|-----------|-------------|----------------------|
| (e.g., ERP) | Inbound | Account | (yes/no/unknown) |
| (e.g., Marketing automation) | Outbound | Contact | (yes/no/unknown) |

### AppExchange Packages

| Package | Version | Person Account Support Confirmed? |
|---------|---------|----------------------------------|
| (package name) | (version) | (yes/no/not checked) |

---

## Apex / Automation Impact Assessment

List all Apex classes and triggers that process Account or Contact records:

| File | Queries Contact? | Queries Account? | IsPersonAccount Check Present? | Action Required |
|------|-----------------|-----------------|-------------------------------|-----------------|
| (e.g., AccountTrigger.trigger) | no | yes | no | Add IsPersonAccount branch |
| | | | | |

---

## Approach

Which pattern from SKILL.md applies? Why?

(e.g., "Pattern: Checking IsPersonAccount Before Processing in Apex — needed because AccountTrigger processes both record types")

---

## Checklist

Copy the relevant checklist items from SKILL.md and tick them as you complete them:

**Enablement prerequisites:**
- [ ] No private Contacts exist (query confirmed count = 0)
- [ ] At least one Account Record Type designated as Person Account type
- [ ] Salesforce Support case submitted (for production enablement)

**Code updates:**
- [ ] All Apex triggers/classes that process Account branch on IsPersonAccount
- [ ] All Contact SOQL queries that must exclude PersonContacts include `Account.IsPersonAccount = false`
- [ ] `before insert` triggers use RecordTypeId check instead of IsPersonAccount

**Reports:**
- [ ] B2B-only Contact reports have `Is Person Account = False` filter
- [ ] Consumer-only reports have `Is Person Account = True` filter

**Integrations:**
- [ ] Inbound integrations create individuals via Account with Person Account RecordTypeId
- [ ] Outbound integrations query Account (not Contact) for person data
- [ ] IsPersonAccount flag handled in all integration payloads

**AppExchange:**
- [ ] All installed packages verified as Person Account compatible

---

## Notes

(Record any deviations from the standard pattern and why. Document any org-specific edge cases, AppExchange compatibility workarounds, or migration decisions.)
