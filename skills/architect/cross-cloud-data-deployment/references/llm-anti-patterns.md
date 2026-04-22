# LLM Anti-Patterns — Cross-Cloud Data Deployment

Common mistakes AI coding assistants make when architecting data flow across Salesforce clouds.

## Anti-Pattern 1: No declared system-of-record per entity

**What the LLM generates:** "Sync Customer bidirectionally between Sales Cloud and Marketing Cloud." No designation of which wins on conflict.

**Why it happens:** The model treats sync as symmetric and skips the ownership question.

**Correct pattern:**

```
Every shared entity has ONE system-of-record per attribute group.
Example: Sales Cloud owns Account name, billing address; Service Cloud
owns Case; Marketing Cloud owns subscription preferences. Conflicts
resolve toward the SoR. Bidirectional sync without SoR = ping-pong
updates.
```

**Detection hint:** An integration spec with "two-way sync" and no "conflict resolution" section.

---

## Anti-Pattern 2: REST sync for cross-cloud CRUD when CDC would do

**What the LLM generates:** Writes a scheduled Apex job that polls Sales Cloud and PUTs to Marketing Cloud every 15 minutes.

**Why it happens:** The model reaches for REST because it is the familiar default; CDC / Platform Events are out of mind.

**Correct pattern:**

```
For record-level CRUD propagation across clouds, use Change Data
Capture. CDC emits field-level changes automatically; no polling;
respects record access. Custom REST sync jobs are for edge cases
where CDC is unavailable or filtering is needed.
```

**Detection hint:** Scheduled Apex class named `*SyncJob` that queries LastModifiedDate and posts to another cloud.

---

## Anti-Pattern 3: Treating Data Cloud as the operational source of truth

**What the LLM generates:** "Let Sales Cloud read customer profile from Data Cloud for each page view."

**Why it happens:** The model sees Data Cloud as the unified profile and assumes it is low-latency enough for operational use.

**Correct pattern:**

```
Data Cloud is the analytical and activation hub, not the operational
SoR. Operational reads happen against Sales/Service; Data Cloud
provides enriched attributes back via Calculated Insights or
Activations (async). Architect for Data Cloud latency (minutes, not
milliseconds).
```

**Detection hint:** A record page with a Lightning component that queries Data Cloud on load.

---

## Anti-Pattern 4: Shared key chosen after data model finalized

**What the LLM generates:** Adds `Global_Customer_Id__c` as a non-External-ID, non-Unique text field after 1M records already exist.

**Why it happens:** The model retrofits keys instead of designing them in.

**Correct pattern:**

```
Shared keys are a design-time decision: External ID + Unique on every
cross-cloud object from day one. If retrofitting, plan for data
repair: de-duplication, key backfill, validation, before enabling any
integration that depends on the key.
```

**Detection hint:** Field metadata with `<externalId>false</externalId>` on fields named like `*_Id__c` used for cross-cloud joining.

---

## Anti-Pattern 5: Marketing Cloud Connect Subscriber Key left at default

**What the LLM generates:** Installs Marketing Cloud Connect and accepts default `Contact.Id` as Subscriber Key.

**Why it happens:** The default works in the demo, so the model leaves it.

**Correct pattern:**

```
Subscriber Key should be an enduring identifier like an email hash or
a Global Customer Id, NOT a cloud-specific Id. Changing Subscriber
Key later requires a mass migration. Decide Subscriber Key at
install time with a cross-cloud identity strategy in view.
```

**Detection hint:** Marketing Cloud Connect config shows Subscriber Key = Contact.Id and Contact has custom owner turnover.
