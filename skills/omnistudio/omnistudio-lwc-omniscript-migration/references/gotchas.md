# Gotchas — OmniStudio LWC OmniScript Migration

## Gotcha 1: Style drift

**What happens:** Colors off after migration.

**When it occurs:** Custom CSS in VF

**How to avoid:** Apply SLDS design tokens + visual regression.


---

## Gotcha 2: Async timing

**What happens:** Remote action timing different in LWC.

**When it occurs:** Chained calls.

**How to avoid:** Use Integration Procedures with queued steps.


---

## Gotcha 3: No opt-out left

**What happens:** Business outage when last VF-only script flips.

**When it occurs:** Aggressive cutover.

**How to avoid:** Phased enablement; pre-flight each script.

