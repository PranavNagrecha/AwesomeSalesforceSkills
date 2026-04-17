# Examples — LWC State Management

## Example 1: Sibling refresh via LMS

**Context:** Edit panel + list panel

**Problem:** Save didn't refresh list

**Solution:**

Publish 'RecordSaved' on channel; list subscribes and refreshApex

**Why it works:** Loose coupling between panels


---

## Example 2: App-wide current region

**Context:** Multi-region switcher

**Problem:** Many components needed region

**Solution:**

Singleton `regionStore.js` with a Set of subscribers; components subscribe in connectedCallback

**Why it works:** No LMS overhead for frequent reads

