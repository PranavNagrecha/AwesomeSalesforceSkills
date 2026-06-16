# Gotchas — LWC Record Picker

Five behaviors of `lightning-record-picker` that catch teams after the
first "Hello, Picker" works — when they try to embed it in a real
surface, scope it with a filter, react to the change event in a
parent, or extend it to polymorphic relationships. Each gotcha has a
documented avoidance path; none are bugs, but all of them fail
silently in ways that are hard to debug from console output alone.

---

## Gotcha 1: Only renders in Lightning Experience, Mobile, and Aura-built Experience sites — fails silently in LWR sites and headless contexts

**What happens:** A team builds a `lightning-record-picker` that
works perfectly on a record page in Lightning Experience, ships it to
a Customer Community, and discovers the picker either renders as a
greyed-out box or doesn't render at all in any **LWR (Lightning Web
Runtime)** Experience Cloud site. The same component embedded as a
content block in an Aura-host wrapper (some legacy record-page
layouts where the host page is still Aura with `c:lwcContainer`
wrappers) sometimes works, sometimes silently no-ops depending on the
container's exposed services. In mobile cards used by Salesforce
Mobile Publisher with restricted UI API access, the picker shows but
its dropdown never populates.

**When it occurs:** Cross-surface deploys, especially when an
LX-tested component is moved into a Customer Community migrated to
LWR, or when a team builds on Aura-host pages without knowing the
container's LDS exposure. Also bites teams writing headless quick
actions (LWC-based) that try to pop a record-picker mid-flow.

**How to avoid:** Confirm the surface BEFORE committing to
`lightning-record-picker`. The platform's supported contexts are
**Lightning Experience, Experience Builder Sites (Aura-based),
and Salesforce Mobile App**. For LWR sites, build a custom picker
using GraphQL queries and a `lightning-combobox` shell (see
`lwc-custom-lookup` skill). For mobile cards with restricted UI
API, fall back to imperative Apex search + manual dropdown. Document
the surface compatibility in your component's `__c.js-meta.xml`
`targets` list so the platform's design-time validator catches the
mismatch.

---

## Gotcha 2: `filter` `criteria` uses the UI API filter JSON shape, not SOQL — wrong shape produces "filter cannot be parsed" silently

**What happens:** Practitioners new to the component pass a filter as
a SOQL string (`"AccountId = '001xx0000003DGbAAM' AND IsDeleted =
false"`) and the picker returns zero matches without raising an
error. Or they construct a filter object but use SOQL-style operator
names (`'='`, `'!='`, `'IN'`) instead of the UI API operator
vocabulary. Or they nest the criteria as a single dict instead of an
array of criterion objects. In every case the dropdown is empty and
console is clean — only the network panel shows a 400 response with
`"filter cannot be parsed"` buried in the response body.

**When it occurs:** Every team's first attempt at a non-trivial
filter, particularly developers migrating from custom SOQL-based
lookups. The error mode is silent because the picker swallows the
parse failure and displays "no results" — there is no toast, no
console warning, and no `error` event dispatch with the parse-failure
details.

**How to avoid:** Use the UI API filter shape exactly as documented.
The required shape is:

```javascript
filter = {
    criteria: [
        { fieldPath: 'AccountId', operator: 'eq', value: this.accountId },
        { fieldPath: 'Email',     operator: 'ne', value: null }
    ],
    filterLogic: '1 AND 2'   // optional; defaults to AND-of-all
};
```

The operator vocabulary is `eq`, `ne`, `lt`, `gt`, `lte`, `gte`,
`in`, `nin`, `like`, `includes`, `excludes` (operator availability
varies by field type — Geolocation fields support only `eq` and
`ne`). When debugging "empty dropdown" issues, the first move is to
open the network panel, find the GraphQL request fired by the
picker, and inspect the response — the parse error message in the
response body tells you which key is wrong.

---

## Gotcha 3: The `change` event payload is on `event.detail.recordId`, NOT `event.target.value`

**What happens:** A parent handler writes `this.selectedId =
event.target.value;` (the reflex from `lightning-input` /
`lightning-combobox` where `value` IS the attribute holding the
selection). The handler runs without error. `this.selectedId` ends
up `undefined`. Downstream code that depends on the Id (Apex calls,
Record Form prefill, navigation) silently no-ops or throws on null
access. The picker itself shows the chip with the selected record,
so the visual feedback looks correct — the parent just can't see the
selection.

**When it occurs:** First time wiring up the change handler, every
time. The error mode is so consistent that LWC code review checklists
in mature orgs include "did you use `event.detail.recordId`?" as a
gate.

**How to avoid:** The `change` event dispatches with `detail = {
recordId }` per the component's API reference — the value is `null`
when the user clears the picker (clicks the X on the chip) and a
record Id when a record is selected. The correct handler:

```javascript
handlePickerChange(event) {
    const recordId = event.detail.recordId;   // string | null
    if (!recordId) {
        // user cleared the selection
        this.selectedId = null;
        return;
    }
    this.selectedId = recordId;
}
```

Two related traps in the same area: (a) the `event.target` reference
exists and has a `.value` getter that reflects the *attribute*-level
`value` (the prop you pass in, not the runtime selection), so
`event.target.value` is technically defined — it's just the *old*
value or the bound prop, not the new selection; (b) jest tests that
mock `event.detail.recordId` correctly will still fail if the parent
code reads from `event.target.value` — write the test against the
documented shape so the bug surfaces in CI.

---

## Gotcha 4: `matching-info.additionalFields` accepts only ONE additional field — extras are silently dropped

**What happens:** Practitioners reading the API docs see
`additionalFields` typed as an array and assume "I can pass three or
four extra search fields." They configure
`additionalFields: [{ fieldPath: 'Email' }, { fieldPath: 'Phone' },
{ fieldPath: 'Title' }]` and find that only `Email` actually
matches — searches against `Phone` or `Title` return no hits. There
is no console warning. The docs phrase the constraint as a passing
sentence; teams miss it.

**When it occurs:** Anytime someone wants a "Google-like" picker that
searches across multiple secondary fields. Also bites migrations from
custom SOSL-based pickers where the SOSL `FIND` clause searched 5+
indexed fields — practitioners assume the base component can do the
same and find it can't.

**How to avoid:** The documented limit is **one `primaryField` plus
one entry in `additionalFields`**, total of two searchable fields per
picker. If the use case genuinely needs more, you have three options:
(a) accept the limitation — pick the highest-value secondary field
(typically `Email` for Contacts, `Industry` for Accounts) and document
the rest as not-searchable; (b) build a *helper field* on the target
object (a Text/Formula field that concatenates Title + Department +
Phone) and use that as the additional search field — works around
the field-count limit at the cost of an extra field per object; (c)
fall back to a custom lookup pattern (see `lwc-custom-lookup`) that
uses SOSL or a custom GraphQL query against any number of fields,
trading the platform's free typeahead/recent-items behavior for
multi-field reach. Note also: encrypted fields cannot appear in
`matching-info` at all, even as the primary — the picker errors out
at first render rather than silently dropping them.

---

## Gotcha 5: Polymorphic lookups (Task.WhatId, Event.WhatId, Lead.OwnerId) need a different attribute — `object-api-name` is not enough

**What happens:** A team builds an Activity-creation modal that needs
the user to set `WhatId` on the new Task. `WhatId` is polymorphic —
it can point to Account, Opportunity, Case, or several dozen other
sObjects. The team configures
`<lightning-record-picker object-api-name="Task" ...>` thinking the
picker will infer the polymorphism from the field metadata. It
doesn't — the picker is built around a *single* concrete
`object-api-name` and only ever searches that one object. Setting
`object-api-name="Account"` gets Accounts but blocks
Opportunities/Cases. Setting `object-api-name` to the parent's API
name (e.g., `"Task"`) gets zero results because the picker queries
the Task object directly, not the polymorphic targets.

**When it occurs:** Any time the underlying lookup field is
polymorphic — Activity `WhatId`/`WhoId`, Lead/Account `OwnerId`
(User vs Queue), CampaignMember `ParentId`, FeedItem `ParentId`,
ContentDocumentLink `LinkedEntityId`, custom polymorphic relationships
that target Person Account vs Business Account.

**How to avoid:** The platform pattern for polymorphic pickers is to
build the picker as a *concrete-object* picker controlled by a
parent-level type selector (radio group, segmented button, or
dropdown that flips `object-api-name`). For Task `WhatId`:

```html
<template>
    <lightning-radio-group
        label="What"
        options={whatTypeOptions}
        value={whatType}
        onchange={handleTypeChange}>
    </lightning-radio-group>
    <lightning-record-picker
        label="Related To"
        object-api-name={whatType}
        onchange={handleWhatChange}>
    </lightning-record-picker>
</template>
```

```javascript
whatTypeOptions = [
    { label: 'Account',     value: 'Account' },
    { label: 'Opportunity', value: 'Opportunity' },
    { label: 'Case',        value: 'Case' }
];
whatType = 'Account';   // default
```

When the user changes the type, the picker re-renders against the
new `object-api-name` and queries that object. The selected
`recordId` from the change handler is then written to `Task.WhatId`
— Salesforce's polymorphic Id format accepts any of the configured
target sObject Ids. The `lwc-recipes` repo's `recordPickerDynamicTarget`
sample is the canonical demonstration of this pattern. Do NOT try to
pass an array of object names to `object-api-name` — the attribute is
typed as a single string and will reject the array silently. Each
polymorphic-target selection requires its own picker render against
one concrete object at a time.
