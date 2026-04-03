# Gotchas - Custom Metadata In Apex

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Tests Quietly Depend On Org Metadata

**What happens:** A test passes because the org already contains the expected `__mdt` records.

**When it occurs:** Teams rely on metadata visibility in tests but never name the dependency.

**How to avoid:** Make expected records explicit in the test design and naming.

---

## Gotcha 2: Runtime DML Thinking

**What happens:** Architects choose CMT for configuration and then treat it like ordinary data in business logic.

**When it occurs:** The read/write difference was never surfaced early.

**How to avoid:** Keep reads in business logic and isolate create or update behavior behind metadata deployment workflows.

---

## Gotcha 3: Package Visibility Drift

**What happens:** A pattern that worked in an unpackaged org breaks once managed-package visibility or subscriber-control rules matter.

**When it occurs:** Teams ignore namespace, protected records, or ownership of edits.

**How to avoid:** Decide early whether records are package controlled or subscriber controlled.
