# Examples — Data Cloud Identity Resolution

## Example 1: Unifying CRM Contacts with Commerce Customers via Email Normalization

**Context:** A retail brand has Salesforce CRM as its system of record for Contact records and a separate e-commerce platform whose customer data is ingested into Data Cloud via the Ingestion API. Both sources contain email addresses, but the CRM stores them in mixed case (from legacy imports) while the commerce platform stores them lowercase. The business wants a single Unified Individual per real customer, combining purchase history from commerce with CRM contact attributes (name, address).

**Problem:** Without identity resolution, a segment filtering on `Unified Individual > Email = 'alice@brand.com'` misses the CRM record stored as `Alice@Brand.com`. The two records stay as separate Individuals, and any activation or AI grounding sees a fragmented view of the same customer.

**Solution:**

```text
Ruleset: EMLR (Email Primary Retail)

Match Rule 1:
  Type: Normalized
  DMO: Contact Point Email
  Field: Email Address
  -- Normalization lowercases both values before comparison.
  -- alice@brand.com == Alice@Brand.com → MATCH

Reconciliation Rules:
  First Name:     Source Priority → CRM (rank 1) > Commerce (rank 2)
  Last Name:      Source Priority → CRM (rank 1) > Commerce (rank 2)
  Email Address:  Most Recent     → whichever source updated the record most recently
  Phone:          Source Priority → CRM (rank 1) > Commerce (rank 2)
```

**Why it works:** The Normalized match type pre-processes both values to lowercase before comparing, so `Alice@Brand.com` and `alice@brand.com` are treated as identical. Source Priority reconciliation ensures the CRM's name values (more likely to be legally accurate) take precedence over the commerce platform's self-reported values while still allowing the email to update from either source.

Post-run validation: After the first ruleset run, navigate to a known customer in Data Cloud's Unified Individuals list and confirm that both the CRM source record and the commerce source record appear as contributing members of the same cluster.

---

## Example 2: Compound Match Rule to Prevent False Positives in a Family-Shared-Phone Scenario

**Context:** A financial services firm's Data Cloud org ingests customer records from a banking CRM and an insurance platform. A significant portion of customers use the same household phone number (a landline or a spouse's mobile) across both systems. An initial single-attribute phone match rule is producing false-positive merges — husband and wife are being unified into a single Unified Individual because they share a phone number but have different email addresses and are separate policy holders.

**Problem:** Single-attribute phone matching fires whenever any two records share a phone number, regardless of name match. In a household-phone scenario, this merges distinct individuals.

**Solution:**

```text
Ruleset: FSVP (FS Voice-Phone)

Remove standalone phone match rule.

Add Compound Match Rule:
  Field 1: Individual > First Name    — Type: Exact
  Field 2: Individual > Last Name     — Type: Exact
  Field 3: Contact Point Phone > Phone Number — Type: Normalized (strips formatting)

All three fields must match for the rule to fire.

Reconciliation Rules (unchanged from prior config):
  Phone Number:   Most Recent
  Email Address:  Source Priority → Banking CRM (rank 1) > Insurance (rank 2)
```

**Why it works:** The Compound rule requires ALL three fields to match simultaneously. Two household members sharing a phone number but having different first names will not satisfy the Compound rule, preventing the false-positive merge. Normalized on phone handles `(555) 123-4567` vs. `5551234567` formatting differences.

Trade-off: Because this Compound rule uses Exact on First Name (not Fuzzy), it will miss records where one source stores "Robert" and the other stores "Bob". If this causes missed merges, add a separate match rule for email (Normalized) alongside the Compound rule — the OR logic means either rule firing creates the merge. Email-based matches will still catch the "Robert"/"Bob" case if both records share the same email.

---

## Anti-Pattern: Creating a Test Ruleset to Experiment, Then Discovering the Slot Is Consumed

**What practitioners do:** A Data Cloud admin creates a second identity resolution ruleset with a temporary name and ad-hoc configuration to test match rule behavior before committing to a production ruleset design. They plan to delete the test ruleset later.

**What goes wrong:** After testing, the admin attempts to create the "real" production ruleset and finds the button disabled — both ruleset slots are consumed (one by the Starter Data Bundle auto-created ruleset, one by the test ruleset). Deleting the test ruleset frees the slot, but the 4-character ruleset ID used in the test cannot be reused (it remains reserved in the org's configuration history). The production ruleset must use a different 4-character ID, and any downstream references to the test ID must be cleaned up.

**Correct approach:** Design the ruleset configuration in full on paper (or in a design document) before creating any ruleset in the org. Treat every ruleset creation as a production-grade decision. Use a sandbox or UAT Data Cloud org for iterative testing if one is available. If testing in production is unavoidable, choose the 4-character ID for the test ruleset as if it were permanent — because the slot consumption effectively makes it so.
