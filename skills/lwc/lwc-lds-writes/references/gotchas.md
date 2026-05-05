# Gotchas — LWC LDS Writes

Non-obvious Salesforce platform behaviors that bite real production code.

## Gotcha 1: `Id` placement in `updateRecord` differs from REST API muscle memory

**What happens:** `updateRecord({ Id: this.recordId, fields: { Industry: 'Tech' } })` throws `INVALID_FIELD_FOR_INSERT_UPDATE` or "Field Id is invalid for record update."

**When it occurs:** Anytime a developer translates from REST `PATCH /sobjects/Account/<id>` (where `Id` is the URL component) into UI API write semantics (where `Id` is a field inside `fields`).

**How to avoid:** Always: `updateRecord({ fields: { Id: this.recordId, Industry: 'Tech' } })`. `Id` is a field; the top level only takes `fields` (and for `createRecord`, `apiName`).

---

## Gotcha 2: schema imports for `fields` keys must use `.fieldApiName`

**What happens:** `fields: { [NAME_FIELD]: 'Acme' }` produces a key like `"[object Object]"` and the UI API rejects the call with `INVALID_FIELD`.

**When it occurs:** When a developer copy-pastes the import-then-use pattern from a `getRecord` example (where the `fields` array takes the import object directly) and forgets that writes need the string field API name.

**How to avoid:** For writes, dereference `.fieldApiName` (a string) on every imported field token:

```javascript
import NAME_FIELD from '@salesforce/schema/Account.Name';
const fields = { [NAME_FIELD.fieldApiName]: 'Acme' };
```

`apiName` for `createRecord` similarly uses `.objectApiName`.

---

## Gotcha 3: read-only / formula / system fields included in `fields` fail the entire write

**What happens:** A developer spreads `...this.account` into `fields`, accidentally including `LastModifiedDate`, a formula, or a `CreatedDate`. The whole `updateRecord` rejects with `INVALID_FIELD_FOR_INSERT_UPDATE`.

**When it occurs:** Anytime the source of `fields` is the wired record itself (which contains every fetched field, including read-only ones).

**How to avoid:** Maintain a `dirtyFields` whitelist explicitly populated from input handlers; never spread the whole record. If you must filter at write time, intersect against `objectInfo.fields[name].updateable`.

---

## Gotcha 4: same-record auto-refresh only covers `getRecord`, not `getRecords`, GraphQL, or Apex wires

**What happens:** A component writes via `updateRecord` and a `@wire(getRecords)` (plural) on the same component still shows stale data.

**When it occurs:** Anytime the component reads multiple records via `getRecords`, or via `lightning/uiGraphQLApi`, or via an `@wire` to an Apex method. LDS auto-refresh after writes only fires for `getRecord` (singular) of the *exact recordId written*.

**How to avoid:** After the write, call `refreshApex(this.wiredApexResult)` for Apex wires, `notifyRecordUpdateAvailable([{ recordId }])` for cross-component / non-singular wires, or restructure to use `getRecord` if a single-record read fits.

---

## Gotcha 5: `INSUFFICIENT_ACCESS_OR_READONLY` is one error code for several access denials

**What happens:** A user without FLS update on a field, without CRUD update on the object, without sharing access to the record, or without the recordtype assigned all see the same error code.

**When it occurs:** Any non-admin profile testing reveals one of the four denial paths, but the JS error gives you no signal which.

**How to avoid:** Don't render denial-specific copy in the toast. Use a generic "you don't have permission to save this change" message and link to a permission-help page. If you need to disambiguate, layer in a separate `getObjectInfo` wire and check `creatable` / `updateable` flags on the object and field before attempting the write.

---

## Gotcha 6: `lightning-record-edit-form` `onsuccess` fires before related-record updates settle

**What happens:** The save handler navigates the user away on `onsuccess`, but a related-record subscription on a sibling component hasn't received the cache-update signal yet, so the user lands on a page showing pre-save data.

**When it occurs:** Any flow that reads from `getRecord` on a parent record after editing a child via `lightning-record-edit-form`, especially on small-screen contexts where animations compound the timing.

**How to avoid:** In `onsuccess`, call `notifyRecordUpdateAvailable` for the related parent recordId(s) explicitly, then navigate. The handler fires when the form's record is committed; siblings need a nudge.

---

## Gotcha 7: `deleteRecord` is fire-and-forget — its Promise resolves to `undefined`

**What happens:** Code that destructures or reads properties from the resolved value of `deleteRecord` throws `TypeError: Cannot read properties of undefined`.

**When it occurs:** When a developer mirrors `updateRecord`'s behavior (which resolves to the updated record DTO) and assumes deletion does the same.

**How to avoid:** `await deleteRecord(recordId);` then use the input `recordId` for any post-delete logic. Don't depend on the resolved value.

---

## Gotcha 8: validation rules with no `errorDisplayField` come back at object level only

**What happens:** A validation rule designed to gate the save (e.g., "Amount must be > 0 if Stage = Closed Won") comes back as an object-level error, not a field-level error. Code that only handles `output.fieldErrors` shows nothing to the user.

**When it occurs:** Anytime the org's validation rules are configured without an explicit error field — common for cross-field rules.

**How to avoid:** Always handle both branches: render `output.errors` as a top-of-form summary or toast, and `output.fieldErrors` next to inputs. Tell admins to set `errorDisplayField` on rules whose error genuinely belongs at a field for better UX.
