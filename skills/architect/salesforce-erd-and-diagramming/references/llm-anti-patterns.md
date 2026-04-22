# LLM Anti-Patterns — Salesforce ERD and Diagramming

Common mistakes AI coding assistants make when generating Salesforce diagrams.

## Anti-Pattern 1: Hand-drafting an ERD without checking metadata

**What the LLM generates:** A Mermaid ERD from training-data memory: Account → Contact, Account → Opportunity, etc., without reading the org's actual schema.

**Why it happens:** The model "knows" the standard object model generically. It does not know the specific org's customizations.

**Correct pattern:**

```
Read the metadata (objects/*.object-meta.xml, field files) before emitting
the diagram. The diagram must reflect THIS org, not a generic Sales Cloud.
```

**Detection hint:** A generated ERD that does not include any custom objects the org actually uses.

---

## Anti-Pattern 2: Drawing polymorphic lookups as single-target arrows

**What the LLM generates:** `TASK }o--|| ACC : WhatId` — pretending Task.WhatId only points to Account.

**Why it happens:** Simple ER syntax does not support polymorphism; the model drops the nuance.

**Correct pattern:**

```
Represent polymorphic lookups (WhatId, WhoId, OwnerId) as a composite
with a note listing the polymorphic targets, or use a sub-diagram.
```

**Detection hint:** A Task or Event relationship drawn as a single arrow to Account or Contact only.

---

## Anti-Pattern 3: Conflating logical and physical ERD

**What the LLM generates:** An "executive ERD" that includes Task, Note, Attachment, ContentDocumentLink.

**Why it happens:** The model dumps everything it sees in metadata.

**Correct pattern:**

```
Pick one: logical (business entities only) or physical (system objects
included). Filter system objects out of executive-facing diagrams.
```

**Detection hint:** A diagram titled "Business ERD" containing ContentVersion, ContentDocumentLink, or FeedItem.

---

## Anti-Pattern 4: Using lookup vs master-detail incorrectly in the diagram syntax

**What the LLM generates:** Uses `||--||` (one-to-one) for every relationship, or inverts parent/child.

**Why it happens:** ER syntax nuance is not well-represented in training.

**Correct pattern:**

```
Master-detail: parent ||--|{ child (strong ownership, cascading delete).
Lookup:        parent |o--o{ child (optional, no cascade).
Get the semantics right; the diagram is read as a contract.
```

**Detection hint:** A diagram where OpportunityLineItem and Opportunity have a dashed lookup edge (they are master-detail).

---

## Anti-Pattern 5: Hand-drawing what can be generated

**What the LLM generates:** Manually types 50 objects and their relationships into Mermaid.

**Why it happens:** Diagram-as-code generation tools for Salesforce are less visible in training; the model defaults to manual construction.

**Correct pattern:**

```
Write or reuse a script that reads objects/*.object-meta.xml and emits
Mermaid or PlantUML. Commit the diagram source and the generator. On
schema change, CI regenerates — no drift.
```

**Detection hint:** Large Mermaid ERDs with no accompanying generator script in the repo.
