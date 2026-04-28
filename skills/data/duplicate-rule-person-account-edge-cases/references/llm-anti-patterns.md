# LLM Anti-Patterns — Duplicate Rule Person Account Edge Cases

Common mistakes AI assistants make when generating or advising on Duplicate / Matching Rules for Person Account orgs. Use these to self-check generated rule XML before deploying.

---

## Anti-Pattern 1: Referencing `Contact.Email` from an Account-built matching rule

**What the LLM generates:** an Account-targeted matching rule with a match item like:

```xml
<matchingRuleItems>
    <fieldName>Contact.Email</fieldName>
    <matchingMethod>Exact</matchingMethod>
</matchingRuleItems>
```

**Why it happens:** the LLM has seen "PA = Account + Contact" and reasons "the email lives on the Contact, so reference Contact.Email." It conflates the *record relationship* with the *match-rule field-resolution scope*. A matching rule resolves field names against the SObject it is built on; cross-object references are only valid in specific cross-object Duplicate Rule slots.

**Correct pattern:**

```xml
<MatchingRule fullName="Account.B2C_Email_Match">
    <booleanFilter>1 AND 2</booleanFilter>
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

**Detection hint:** in any `Account.*.matchingRule-meta.xml`, grep for `<fieldName>Contact\.` — should never appear. The skill-local checker reports this as P0.

---

## Anti-Pattern 2: Omitting the `IsPersonAccount` filter in a mixed B2B + B2C org

**What the LLM generates:** a rule that matches on `Name` + `BillingStreet` with no PA gate, in an org where the LLM was told B2B and B2C coexist.

**Why it happens:** the LLM follows the explicit prompt ("match on name and address") and does not infer the implicit gate ("only within the same record-type universe"). B2B training data dominates and biases toward unfiltered Name matching.

**Correct pattern:**

```xml
<MatchingRule fullName="Account.B2C_Name_Address_Match">
    <booleanFilter>1 AND 2 AND 3</booleanFilter>
    <matchingRuleItems>
        <fieldName>FirstName</fieldName>
        <matchingMethod>FuzzyFirstName</matchingMethod>
    </matchingRuleItems>
    <matchingRuleItems>
        <fieldName>LastName</fieldName>
        <matchingMethod>FuzzyLastName</matchingMethod>
    </matchingRuleItems>
    <matchingRuleItems>
        <fieldName>IsPersonAccount</fieldName>
        <matchingMethod>Exact</matchingMethod>
    </matchingRuleItems>
</MatchingRule>
```

**Detection hint:** in any Account-targeted matching rule on a PA-enabled org, the absence of an `IsPersonAccount` field item is a P0. The skill-local checker reports it.

---

## Anti-Pattern 3: Wrapping email match in `LOWER()` "to fix case sensitivity"

**What the LLM generates:** a Duplicate Rule with a formula condition like:

```text
LOWER(PersonEmail) == LOWER($PreviousValue.PersonEmail)
```

or a match item that points at a formula field `PersonEmail_Lower__c`.

**Why it happens:** training data is full of database-flavoured advice "always normalize case before comparing emails." The LLM does not know that Salesforce's `Exact` matching method on an Email-type field is already case-insensitive.

**Correct pattern:** leave the match item as plain `Exact` on `PersonEmail`. Do not add `LOWER()` wrappers. Do not create a `_Lower__c` formula field.

```xml
<matchingRuleItems>
    <fieldName>PersonEmail</fieldName>
    <matchingMethod>Exact</matchingMethod>
</matchingRuleItems>
```

**Detection hint:** any `LOWER(` token inside a duplicate rule's `<formulaCondition>`, or any formula field with `_Lower__c` referenced from a match item, is suspicious. Email matching does not need case normalization on Salesforce.

---

## Anti-Pattern 4: Hand-rolling Levenshtein / Jaro-Winkler in a formula field

**What the LLM generates:** a custom formula field `Name_Soundex__c` or `Name_Levenshtein__c` that approximates string distance using nested `MID()` and `IF()` calls, then a match item that compares Exact on the formula field.

**Why it happens:** the LLM "knows" fuzzy matching algorithms by name and reaches for them when asked for fuzzy match, ignoring that Salesforce ships tuned, indexed fuzzy methods (`FuzzyFirstName`, `FuzzyLastName`, `FuzzyStreet`).

**Correct pattern:**

```xml
<matchingRuleItems>
    <fieldName>FirstName</fieldName>
    <matchingMethod>FuzzyFirstName</matchingMethod>
</matchingRuleItems>
<matchingRuleItems>
    <fieldName>LastName</fieldName>
    <matchingMethod>FuzzyLastName</matchingMethod>
</matchingRuleItems>
```

**Detection hint:** any formula field referenced from a matching rule whose name contains `Levenshtein`, `Jaro`, `Soundex`, `Metaphone`, or `Distance` is almost certainly reinventing a platform feature. Use the platform fuzzy methods.

---

## Anti-Pattern 5: Building the Lead-convert dedupe on the Lead-targeted rule alone

**What the LLM generates:** when asked "stop duplicate Person Accounts from being created on lead convert," the LLM writes a Lead-targeted Duplicate Rule with a Lead-vs-Lead matching rule and declares victory.

**Why it happens:** the LLM follows the surface request ("Lead convert dedupe") without reasoning about *which SObject the convert insert lands on*. Convert that produces a PA inserts into Account; the rule that fires is the Account-targeted one.

**Correct pattern:** either (a) two duplicate rules — Lead-targeted for pre-convert hygiene, Account-targeted (PA-aware) for the convert moment — or (b) a single Lead-targeted rule with cross-object match items pointing at `Account.PersonEmail`:

```xml
<DuplicateRule fullName="Lead.Convert_Time_Email">
    <duplicateRuleMatchingRules>
        <matchingRule>Lead.Email_Match</matchingRule>
        <objectName>Lead</objectName>
    </duplicateRuleMatchingRules>
    <duplicateRuleMatchingRules>
        <matchingRule>Account.B2C_Email_Match</matchingRule>
        <objectName>Account</objectName>
    </duplicateRuleMatchingRules>
    <isActive>true</isActive>
</DuplicateRule>
```

**Detection hint:** if a generated rule set claims to handle "lead convert duplicates" but contains zero Account-targeted Duplicate Rule files, it is broken. Cross-check `objects/Account/duplicateRules/` for at least one PA-aware active rule.

---

## Anti-Pattern 6: Treating PA delete as "delete the Contact" for GDPR

**What the LLM generates:** an erase / right-to-be-forgotten Apex method that does:

```apex
delete [SELECT Id FROM Contact WHERE Email = :request.email AND Account.IsPersonAccount = true];
```

**Why it happens:** the LLM mirrors the B2B Contact-delete pattern. It does not know that the Person Contact (`003`) is structurally tied to its Account (`001`) and cannot be deleted independently.

**Correct pattern:**

```apex
// Delete the Account side; the platform cascades to the Person Contact.
delete [SELECT Id FROM Account WHERE PersonEmail = :request.email AND IsPersonAccount = true];
```

**Detection hint:** any erase / privacy job that targets `Contact` `WHERE Account.IsPersonAccount = true` is wrong. Target the Account row.

---

## Anti-Pattern 7: Using `matchingMethod = Exact` on a phone field

**What the LLM generates:** a match item on `PersonMobilePhone` with `matchingMethod = Exact`, on the assumption that "exact is the safest default."

**Why it happens:** "Exact" sounds like the most conservative choice. The LLM does not know about the platform's `Phone` matching method that strips formatting.

**Correct pattern:**

```xml
<matchingRuleItems>
    <fieldName>PersonMobilePhone</fieldName>
    <matchingMethod>Phone</matchingMethod>
</matchingRuleItems>
```

**Detection hint:** any phone-typed field (`*Phone`) with `matchingMethod = Exact` should be flagged. The skill-local checker reports this as P1.
