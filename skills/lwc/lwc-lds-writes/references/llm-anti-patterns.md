# LLM Anti-Patterns — LWC LDS Writes

Common mistakes AI coding assistants make when generating or advising on Lightning Data Service write code. These help the consuming agent self-check its own output before claiming a solution.

## Anti-Pattern 1: putting `Id` at the top level of `recordInput` for `updateRecord`

**What the LLM generates:**

```javascript
await updateRecord({
    Id: this.recordId,
    fields: { Industry: 'Technology' }
});
```

**Why it happens:** REST API training data dominates — `PATCH /sobjects/Account/<id>` puts the Id in the URL and the body has only the writable fields. LLMs translate that mental model directly into LDS syntax, which uses a different shape.

**Correct pattern:**

```javascript
await updateRecord({
    fields: { Id: this.recordId, Industry: 'Technology' }
});
```

**Detection hint:** grep generated code for `updateRecord({\s*Id:`. Any match with `Id` outside `fields` is the wrong shape.

---

## Anti-Pattern 2: using a `@salesforce/schema` import object directly as a `fields` key

**What the LLM generates:**

```javascript
import NAME_FIELD from '@salesforce/schema/Account.Name';
await updateRecord({
    fields: { Id: this.recordId, [NAME_FIELD]: 'Acme' }
});
```

**Why it happens:** LLMs see `getRecord` examples that pass schema imports directly inside the `fields` array (where they're consumed object-style by the wire adapter) and assume writes follow the same pattern.

**Correct pattern:**

```javascript
import NAME_FIELD from '@salesforce/schema/Account.Name';
await updateRecord({
    fields: { Id: this.recordId, [NAME_FIELD.fieldApiName]: 'Acme' }
});
```

**Detection hint:** any `[X_FIELD]` (or `[X_OBJECT]`) used as a computed key without `.fieldApiName` / `.objectApiName` is wrong for write paths.

---

## Anti-Pattern 3: handling `updateRecord` rejections as plain strings

**What the LLM generates:**

```javascript
} catch (err) {
    this.dispatchEvent(new ShowToastEvent({
        title: 'Error',
        message: err.message,
        variant: 'error'
    }));
}
```

**Why it happens:** Generic JS error handling overrides domain knowledge. `err.message` is often `"Invalid record"` — useless to the user — when the structured envelope has the actual field-level message.

**Correct pattern:**

```javascript
} catch (err) {
    const output = err?.body?.output ?? {};
    const fieldErrors = output.fieldErrors ?? {};
    const objectErrors = (output.errors ?? []).map(e => e.message);
    // map fieldErrors to inputs, render objectErrors as a summary
}
```

**Detection hint:** `err.message` or `err.toString()` in an LDS write catch block. UI API errors are objects, not strings.

---

## Anti-Pattern 4: assuming `lightning/uiRecordApi` has a bulk write API

**What the LLM generates:**

```javascript
import { updateRecords } from 'lightning/uiRecordApi';   // does not exist
await updateRecords(rows.map(r => ({ fields: { Id: r.id, Status__c: r.status } })));
```

or

```javascript
for (const row of rows) {
    await updateRecord({ fields: { Id: row.id, Status__c: row.status } });
}
```

**Why it happens:** LLMs pattern-match from REST batch APIs and Apex `Database.update(records)`. UI API has no array form, and the loop variant is functionally one HTTP call per record.

**Correct pattern:** for >1 record, route the call through an `@AuraEnabled` Apex method that does a single bulk DML and returns `Database.SaveResult[]`. Reserve LDS writes for single-record user gestures.

**Detection hint:** any `updateRecords` (plural) import — does not exist. Any `await` inside a `for...of` calling `updateRecord` — should be a bulk Apex call.

---

## Anti-Pattern 5: assuming auto-refresh covers `getRecords`, GraphQL, or Apex wires

**What the LLM generates:** "After `updateRecord`, your wired data refreshes automatically — no extra code needed."

**Why it happens:** This is *true* for `@wire(getRecord, ...)` of the same recordId in the same component. LLMs over-generalize that to all wire adapters.

**Correct pattern:**

| Wire | Refresh after LDS write |
|---|---|
| `@wire(getRecord)` same recordId, same component | Auto |
| `@wire(getRecords)` (plural) | `notifyRecordUpdateAvailable([{ recordId }])` |
| `@wire(graphql)` | `refreshGraphQL(wiredResult)` |
| `@wire(apexMethod)` | `refreshApex(wiredResult)` |
| Any wire in a *different* component | `notifyRecordUpdateAvailable` |

**Detection hint:** any answer that claims "wired data refreshes automatically" without naming the wire adapter is incomplete. Auto-refresh is a `getRecord`-singular-same-component-only behavior.

---

## Anti-Pattern 6: spreading the wired record into `fields`

**What the LLM generates:**

```javascript
const fields = { ...this.account, Industry: 'Tech' };
await updateRecord({ fields });
```

**Why it happens:** Standard JS pattern; readable; doesn't acknowledge that wired records contain read-only fields.

**Correct pattern:** maintain an explicit dirty-fields whitelist:

```javascript
const fields = { Id: this.recordId, Industry: 'Tech' };
await updateRecord({ fields });
```

**Detection hint:** spreading any wired record (`...this.account`, `...this.record.fields`) into `fields`. Any `LastModifiedDate`, `CreatedDate`, formula field, or system field included will reject the entire write.
