# Gotchas — Lookup And Relationship Design

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: On a two-master-detail object, `relationshipOrder` quietly decides ownership

**What happens:** An object with two master-detail relationships (a junction object) must designate one parent primary and the other secondary, carried in the field's Metadata API `relationshipOrder`: "Junction objects must define one parent object as primary (0), the other as secondary (1). The definition of primary or secondary affects delete behavior and inheritance of look and feel, and record ownership for junction objects." The two fields look symmetrical in Setup, but one of them is deciding who owns every junction record.

**When it occurs:** On any custom object carrying two master-detail fields — supported since API version 11.0 — and most painfully when a data-model refactor loosens one parent to a lookup, or when someone assumes the junction inherits its owner from whichever parent reads as "the main one."

**How to avoid:** Settle which parent should govern ownership and deletion before either field ships, set `relationshipOrder` explicitly in the field metadata, and record the choice in the relationship design doc. Plan for the second-order effect too: "Custom objects on the detail side of a master-detail relationship can't have sharing rules, manual sharing, or queues, because these elements require the Owner field" — so no amount of sharing configuration on the junction compensates for naming the wrong primary.

---

## Gotcha 2: TODO: Name

**What happens:** TODO: describe the unexpected behavior

**When it occurs:** TODO: describe the conditions

**How to avoid:** TODO: fix or prevention

---

## Gotcha 3: TODO: Name

**What happens:** TODO: describe the unexpected behavior

**When it occurs:** TODO: describe the conditions

**How to avoid:** TODO: fix or prevention
