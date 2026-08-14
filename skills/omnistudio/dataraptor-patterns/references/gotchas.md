# DataRaptor Patterns — Gotchas

## 1. Turbo Extract Is A Narrow Optimization

Teams often treat Turbo Extract like a default performance upgrade. It is not a faster Extract with the same surface. Salesforce states: "Because a Data Mapper Turbo Extract is a simpler type, it doesn't have formulas or mappings." And separately: "You can't use formulas, custom JSON, default values, and transformations on a Data Mapper Turbo Extract." Its configuration surface is the extraction object, filters, the fields to return (including fields from related parent objects), and Options.

Avoid it:
- Use it for simple single-object reads only.
- Switch back to Extract the moment a formula, a default value, custom output JSON, or a transformation enters the requirement — a Turbo Extract has no Output tab to configure one in.

## 2. Mapping Complexity Hides Asset Drift

The DataRaptor may still function while becoming impossible to maintain confidently.

Avoid it:
- Keep names and output shapes deliberate.
- Split read, transform, and write responsibilities clearly.

## 3. Load Assets Are Production Write Surfaces

Because they are declarative, teams sometimes under-review them.

Avoid it:
- Treat the input contract like any other write API.
- Remove brittle assumptions such as hardcoded record IDs.

## 4. Orchestration Logic Belongs Elsewhere

The urge to keep everything in one OmniStudio layer can turn a mapping asset into a pseudo-service layer.

Avoid it:
- Move sequencing and multi-step coordination into Integration Procedures.
- Use Apex where OmniStudio no longer fits cleanly.

## 5. Transform And Load Cannot Query Salesforce

Designs sometimes assume a Load can look up the record it is about to update, or that a Transform can enrich a payload from Salesforce. Neither can: "The Data Mapper Transform and Load types don't include queries because they're not retrieving data from Salesforce objects."

Avoid it:
- Fetch first, then reshape or write — a Data Mapper Extract, an HTTP action in an Integration Procedure, or the calling OmniScript supplies the data these types consume.
- Resolve the target record with an upsert key on the Load instead of an imaginary query step inside it.

---

## 6. A Six-Object Extract Used as a Callout Body Is a God DataRaptor

**What happens:** One Extract joins User, Contact, Transaction, Notice, RecordType, and a limit object to build an HTTP body. Every extra object is a SOQL inside the IP's transaction. Turbo cannot replace it (no formulas/mappings).

**When it occurs:** "One DR for the Mule payload."

**How to avoid:** Keep Extract object count small. Fan-out belongs in separate DRs or relationship queries. The IP orchestrates. `EnforceDMFLSAndDataEncryption` must be true or this DR is also an FLS bypass — see `omnistudio-security` §10.

---

## 7. Data Mapper Versioning Is One-Way

**What happens:** `enableOmniStudioDrVersion` creates versioned DRs and, once on, is reported as not disableable. Teams enable it casually then inherit an ops tax.

**How to avoid:** Decide deliberately. If off, use git/naming for DR change control. If on, treat versions like OmniScript versions (one active, delete superseded in guest orgs).
