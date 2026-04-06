# LLM Anti-Patterns — Lead Management and Conversion

Common mistakes AI coding assistants make when generating or advising on Lead Management and Conversion.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Claiming All Lead Fields Automatically Transfer on Conversion

**What the LLM generates:** "When you convert a Lead in Salesforce, all field values are automatically mapped to the resulting Contact, Account, and Opportunity."

**Why it happens:** LLMs trained on general Salesforce content frequently see the conversion workflow described at a high level without the caveat that field mapping is explicit and manual. The phrase "lead conversion" in training data often describes the business process, not the technical mapping mechanics.

**Correct pattern:**

```
Only standard fields have default mappings. Every custom Lead field must be
explicitly mapped in Object Manager > Lead > Fields & Relationships > Map Lead Fields.
Unmapped custom fields are silently dropped on conversion with no error or warning.
```

**Detection hint:** Any statement containing "all fields", "automatically maps", or "transfers the data" without qualifying "only mapped fields" should be flagged as potentially incorrect.

---

## Anti-Pattern 2: Suggesting Auto-Response Rules Work Without an Assignment Rule

**What the LLM generates:** "You can set up a Lead Auto-Response Rule in Setup to automatically send a welcome email to all web-to-lead submissions. Configure the rule criteria and email template and it will fire for every submission."

**Why it happens:** Auto-response rules and assignment rules are separate configuration objects in Setup. LLMs treat them as independent because they appear as sibling items in the navigation. The coupling — that auto-response only fires when assignment also fires — is a runtime dependency not visible in the UI structure.

**Correct pattern:**

```
Auto-response rules only send email when an active assignment rule also fires
on the same record. If no assignment rule is active or no entry matches the
incoming lead, the auto-response email is silently skipped regardless of whether
the auto-response criteria match.

Always verify an active assignment rule with a catch-all entry exists before
configuring auto-response rules.
```

**Detection hint:** Any recommendation to configure auto-response rules that does not mention the assignment rule dependency is incomplete and likely to produce a silently broken configuration.

---

## Anti-Pattern 3: Treating the 500/Day Web-to-Lead Limit as a Calendar-Day Reset

**What the LLM generates:** "Web-to-Lead has a 500 lead per day limit. If you hit the limit, submissions will be blocked until the next day when the counter resets."

**Why it happens:** "Per day" is commonly interpreted as midnight-to-midnight in most rate-limit contexts. Salesforce's rolling 24-hour window behavior is a platform-specific nuance not well represented in general training data.

**Correct pattern:**

```
The web-to-lead limit is 500 submissions per rolling 24-hour window, not per
calendar day. If the limit is hit at 2 PM, it does not clear at midnight — it
clears 24 hours after the first submission in the batch (around 2 PM the next day).

For orgs expecting sustained high volume, supplement or replace web-to-lead with
API-based Lead insertion (REST/SOAP), which has no equivalent rolling daily limit.
```

**Detection hint:** Any mention of "resets at midnight", "resets daily", or "next day" in the context of the web-to-lead limit should be corrected to "rolling 24-hour window."

---

## Anti-Pattern 4: Recommending Picklist Mapping Without Verifying Value Parity

**What the LLM generates:**

```
// Map Lead.Industry (picklist) to Account.Industry (picklist) in field mapping.
// This will transfer the industry value on conversion.
```

**Why it happens:** Field mapping configuration between picklist fields appears straightforward in the UI. LLMs do not surface the platform behavior that a picklist value which exists on Lead but not on the target field will be silently dropped rather than causing a validation error.

**Correct pattern:**

```
When mapping Lead picklist fields to target object picklist fields:
1. Verify that every picklist value on the Lead field also exists on the target field.
2. Use Global Value Sets (Setup > Picklist Value Sets) for picklists mapped across
   Lead and its conversion targets to keep values synchronized automatically.
3. After any picklist value change on a mapped Lead field, apply the same change
   to the target field immediately.

Value mismatches cause silent transfer failures — the target field is left blank
with no error during conversion.
```

**Detection hint:** Any picklist-to-picklist mapping recommendation that does not mention value parity verification or Global Value Sets is incomplete.

---

## Anti-Pattern 5: Not Accounting for the Default Web-to-Lead Creator User in Duplicate Rules

**What the LLM generates:** "To prevent duplicate leads from web-to-lead submissions, enable your existing duplicate matching rule on the Lead object. It will automatically deduplicate incoming submissions."

**Why it happens:** Duplicate rules and web-to-lead are conceptually separate features. LLMs recommend enabling duplicate rules on Lead without understanding that web-to-lead submissions run in the context of the Default Web-to-Lead Creator system user — and if that user is not excluded from the rule's bypass, Block-action duplicate rules silently reject submissions rather than creating leads.

**Correct pattern:**

```
When applying duplicate matching rules to the Lead object in an org using web-to-lead:
1. Identify rules where Action = "Block".
2. Confirm the Default Web-to-Lead Creator user is excluded from the matching rule
   via profile-based bypass or sharing bypass.
3. If blocking is required for web submissions, consider changing the action to
   "Allow" with "Alert" so duplicate submissions are flagged but still created,
   then merge duplicates as a separate operational process.

A Block-action duplicate rule that matches an incoming web-to-lead submission will
silently discard the submission. The submitter sees the confirmation page but no
Lead is created and no admin notification is generated.
```

**Detection hint:** Any recommendation to "enable duplicate rules on Lead" without mentioning the Default Web-to-Lead Creator bypass concern should be treated as potentially causing silent submission loss.

---

## Anti-Pattern 6: Advising Admins to Hand-Edit Generated Web-to-Lead Field Names

**What the LLM generates:**

```html
<!-- Add this field to your web-to-lead form for lead source tracking -->
<input type="hidden" name="lead_source" value="Website">
```

**Why it happens:** LLMs familiar with web forms default to human-readable field name patterns. Salesforce web-to-lead custom fields require the field's 15- or 18-character ID (e.g., `00N000000000001`) as the `name` attribute, not the API name or a human-readable label.

**Correct pattern:**

```html
<!-- Custom fields use the Salesforce field ID, not the API name -->
<!-- Generate the form in Setup > Web-to-Lead to get the correct IDs -->
<input type="hidden" name="00N5i00000XXXXX" value="Website">
```

**Detection hint:** Any web-to-lead form HTML with `name` values using underscores or human-readable labels for custom fields (rather than 15–18 character Salesforce IDs beginning with `00N`) is using incorrect field names that will be silently ignored by Salesforce.
