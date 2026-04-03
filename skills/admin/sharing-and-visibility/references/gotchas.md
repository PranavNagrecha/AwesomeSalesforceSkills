# Gotchas: Sharing and Visibility

---

## `View All` and `Modify All` Bypass Everything You Thought You Designed

**What happens:** An admin insists the object is private. A user still sees every record. The reason is not the sharing rule - it is an object-level bypass permission.

**When it bites you:** Legacy profiles, copied permission sets, admin-lite personas.

**How to avoid it:** Audit object `View All` / `Modify All` and system `View All Data` / `Modify All Data` before debugging sharing rules.

**Example:**
```text
Object OWD = Private
Permission Set = Opportunity View All
Result = user sees every Opportunity anyway
```

---

## Manual Sharing Becomes Invisible Technical Debt

**What happens:** Access works today because admins shared a few records manually months ago. Nobody remembers that, so future debugging gets misdirected.

**When it bites you:** Escalations, executive exceptions, and one-off customer access requests.

**How to avoid it:** Treat manual sharing as temporary. Report on it, review it, and replace recurring patterns with a declarative model.

**Example:**
```text
Recurring support request: "Share this Account with the partner team."
Fix: public group + owner-based or criteria-based rule
```

---

## Role Hierarchy Does Not Solve Cross-Team Access

**What happens:** Business users expect peers in another function to see the same records because they collaborate. The hierarchy does not grant that access.

**When it bites you:** Sales-to-service, service-to-legal, or region-to-region collaboration models.

**How to avoid it:** Use public groups and sharing rules for sideways access. Keep the hierarchy aligned to reporting structure, not every collaboration scenario.

**Example:**
```text
Manager access = automatic through hierarchy
Peer-team access = requires sharing rule or team membership
```

---

## Criteria-Based Sharing at Volume Has a Cost

**What happens:** A rule based on fields like region, status, and business unit looks elegant until large data changes cause sharing recalculation pain.

**When it bites you:** Mass updates, ownership changes, and large backfills.

**How to avoid it:** Keep criteria selective, reduce unnecessary rules, and test recalculation impact before major data events.

**Example:**
```text
Mass update 500,000 records
Criteria-based rule depends on Status__c
Result: recalculation becomes part of the operational risk
```
