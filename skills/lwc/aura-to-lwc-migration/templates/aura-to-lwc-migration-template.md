# Aura to LWC Migration — Work Template

Use this template when planning and executing the migration of an Aura component to LWC.

---

## Scope

**Skill:** `aura-to-lwc-migration`

**Component being migrated:** (fill in the Aura component name)

**Request summary:** (fill in what the user asked for)

**Migration strategy:** [ ] Big-bang rewrite  [ ] Incremental (coexistence with LMS bridge)

---

## Pre-Migration Audit

Complete this section before writing any LWC code.

### Aura Component Attributes

| Attribute Name | Type | Default | Visibility (public/private) | LWC Equivalent |
|---|---|---|---|---|
| `exampleAttr` | `String` | `null` | public | `@api exampleAttr` |
| | | | | |

### Aura Event Surface

| Event Name | Type (COMPONENT / APPLICATION) | Parameters | LWC Replacement |
|---|---|---|---|
| `exampleEvent` | APPLICATION | `{ recordId: String }` | LMS channel `Example__c` |
| `itemSelected` | COMPONENT | `{ id: String, label: String }` | `CustomEvent('itemselected', { detail: ... })` |
| | | | |

### Navigation Calls

| Aura Navigation Pattern | Parameters | LWC NavigationMixin Replacement |
|---|---|---|
| `force:navigateToSObject` | `recordId` | `standard__recordPage` with `actionName: view` |
| | | |

### Lifecycle Hooks Used

| Aura Hook | Purpose | LWC Equivalent |
|---|---|---|
| `init` | | `connectedCallback` |
| `afterRender` | | `renderedCallback` (guard with `hasRendered` flag) |
| `destroy` | | `disconnectedCallback` |

### $A API Calls

| $A Call | Purpose | LWC Replacement |
|---|---|---|
| `$A.enqueueAction(action)` | Server call | Imperative Apex import + `async/await` |
| `$A.getCallback(fn)` | Re-enter Aura lifecycle | Remove — not needed in LWC |
| `$A.createComponent(...)` | Dynamic component | Conditional rendering or slot-based composition |

### Dynamic Component Creation

[ ] None — the component does not use `ltng:dynamicComponent` or `$A.createComponent`
[ ] Present — describe the pattern and planned LWC replacement below:

(describe here)

---

## LMS Channel Design (if applicable)

Fill this section if any Aura application events are being replaced.

**Channel name:** `________.messageChannel-meta.xml`

**Fields:**

| Field Name | Type | Description |
|---|---|---|
| | | |

**Publishers (Aura and/or LWC):**
-

**Subscribers (Aura and/or LWC):**
-

---

## LWC Component Structure

**Component name:** `c/____________`

**Target surfaces (`*.js-meta.xml` targets):**
- [ ] `lightning__AppPage`
- [ ] `lightning__RecordPage`
- [ ] `lightning__HomePage`
- [ ] `lightningCommunity__Page`
- [ ] Other: ___________

**Public API (`@api` properties):**

```javascript
@api recordId;
@api objectApiName;
// add more
```

**Wire adapters or imperative Apex calls:**

```javascript
// @wire or import statements
```

---

## Parity Verification Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] All `aura:attribute` values ported to `@api` or reactive private properties
- [ ] Aura application events replaced with LMS channel (channel definition deployed)
- [ ] `force:navigate*` calls replaced with `NavigationMixin.Navigate`
- [ ] Aura lifecycle hooks mapped to correct LWC hooks
- [ ] `.js-meta.xml` `targets` array matches deployment surfaces
- [ ] Shadow DOM event propagation verified (`composed: true` where needed)
- [ ] No `$A.*` calls remain in LWC JavaScript
- [ ] Dynamic component creation patterns explicitly refactored or deferred with tracked backlog item
- [ ] `renderedCallback` guarded with `hasRendered` flag if used
- [ ] CustomEvent names are all lowercase

---

## Side-by-Side Functional Test Notes

| Feature / Interaction | Aura Behavior | LWC Behavior | Pass / Fail |
|---|---|---|---|
| | | | |

---

## Notes

(Record any deviations from the standard migration pattern and why.)
