# LLM Anti-Patterns — LWC GraphQL Wire

Common mistakes AI coding assistants make when generating or advising on LWC GraphQL Wire code.
These patterns help the consuming agent self-check its own output before returning it to the user.

## Anti-Pattern 1: JS Interpolation Inside The `gql` Literal

**What the LLM generates:**

```javascript
@wire(graphql, {
    query: gql`
        query {
            uiapi {
                query {
                    Account(where: { Id: { eq: "${this.recordId}" } }) {
                        edges { node { Id Name { value } } }
                    }
                }
            }
        }
    `
})
```

**Why it happens:** LLMs pattern-match `gql` onto generic JavaScript template-literal idioms and treat `${}` interpolation as the way to pass dynamic values. In Apollo-style client code, interpolation into `gql` is also discouraged but at least possible; on Salesforce it is silently non-reactive.

**Correct pattern:**

```javascript
get variables() {
    return { recordId: this.recordId };
}

@wire(graphql, {
    query: gql`
        query AccountById($recordId: ID) {
            uiapi {
                query {
                    Account(where: { Id: { eq: $recordId } }, first: 1) {
                        edges { node { Id Name { value } } }
                    }
                }
            }
        }
    `,
    variables: '$variables',
    operationName: 'AccountById'
})
handleResult(result) {
    this.wiredResult = result;
}
```

**Detection hint:** `\$\{` appearing inside a `gql\`...\`` literal where the interpolated value is a **reactive per-record filter** (a record id, a user-changed filter). On v1 any such match is a bug. On v2, interpolation is a legitimate feature for **dynamic query construction** — varying the query's structure (an object name, a field set) at runtime — so a v2 match is only a bug when it carries reactive filter data that should be a declared `$` variable. Scope the flag by module and by what the interpolation carries, not by the presence of `${` alone.

---

## Anti-Pattern 2: Accessing Fields Without `.value`

**What the LLM generates:**

```html
<template>
    <p>{record.Name}</p>
    <p>{record.Amount}</p>
</template>
```

**Why it happens:** LLMs trained on `getRecord` + `getFieldValue` patterns expect flat scalars. The UI API GraphQL response wraps every field as `{ value, displayValue }`, which the model forgets.

**Correct pattern:**

```html
<template>
    <p>{record.Name.value}</p>
    <p>{record.Amount.displayValue}</p>
</template>
```

**Detection hint:** In an HTML template associated with a `graphql` wire, regex `\{record\.[A-Z]\w+\}` that does not end in `.value`, `.displayValue`, or another subfield. Bare `{record.FieldName}` is the tell.

---

## Anti-Pattern 3: Calling `refreshApex` On A GraphQL Wired Result

**What the LLM generates:**

```javascript
import { refreshApex } from '@salesforce/apex';
import { gql, graphql } from 'lightning/uiGraphQLApi';

async handleSaved() {
    await refreshApex(this.wiredResult); // wrong helper for graphql
}
```

**Why it happens:** `refreshApex` is by far the most common refresh primitive in LWC training data, so the model reaches for it reflexively even when the wire is not an Apex wire.

**Correct pattern (v1):**

```javascript
import { gql, graphql, refreshGraphQL } from 'lightning/uiGraphQLApi';

async handleSaved() {
    await refreshGraphQL(this.wiredResult);
}
```

**Correct pattern (v2):** there is no `refreshGraphQL` — refresh lives on the emitted result.

```javascript
import { gql, graphql } from 'lightning/graphql';

async handleSaved() {
    await this.graphqlResult.refresh();
}
```

**Detection hint:** Any file that imports both `refreshApex` from `@salesforce/apex` and `graphql` from a GraphQL module, or any call to `refreshApex` with an argument that was populated by a `graphql` wire handler. Also flag `refreshGraphQL` imported from `lightning/graphql` (v2) — it does not exist there; v2 uses `result.refresh()`.

---

## Anti-Pattern 4: Putting A `mutation` Block Inside The Wired Query

**What the LLM generates:**

```javascript
@wire(graphql, {
    query: gql`
        mutation UpdateAccount($id: ID!, $name: String!) {
            updateAccount(input: { id: $id, name: $name }) { Id }
        }
    `
})
wiredThing;
```

**Why it happens:** Other GraphQL ecosystems (Apollo, Relay, GitHub, Shopify) run queries and mutations through the same client, so the model embeds a mutation into the wired query. On Salesforce the **wire is read-only** on both modules — a mutation in the wired query fails.

**Correct pattern — v2 (`lightning/graphql`, Spring '26+):** writes are a separate `executeMutation` call, not part of the wire.

```javascript
import { gql, graphql, executeMutation } from 'lightning/graphql';

const UPDATE_CONTACT = gql`
    mutation UpdateContactTitle($input: ContactUpdateInput) {
        uiapi { ContactUpdate(input: $input) { Record { Id Title { value } } } }
    }
`;

async save() {
    await executeMutation({
        query: UPDATE_CONTACT,
        variables: { input: { Id: this.recordId, Contact: { Title: this.newTitle } } }
    });
    await this.graphqlResult.refresh(); // create/update need refresh; delete does not
}
```

**Correct pattern — v1 (`lightning/uiGraphQLApi`, Mobile Offline):** no write path; use UI API.

```javascript
import { updateRecord } from 'lightning/uiRecordApi';
import { gql, graphql, refreshGraphQL } from 'lightning/uiGraphQLApi';

async save() {
    await updateRecord({ fields: { Id: this.recordId, Title: this.newTitle } });
    await refreshGraphQL(this.wiredResult);
}
```

**Detection hint:** The keyword `mutation` inside a `gql` literal that is passed to `@wire(graphql, ...)` — that is always wrong. A `mutation` literal passed to `executeMutation` on v2 is correct. The exact mutation field/input names come from the org's UI API GraphQL schema; introspect it rather than inventing Apollo-style `updateAccount(input:)` shapes.

---

## Anti-Pattern 5: Treating `edges` As The Whole Result, Skipping `pageInfo`

**What the LLM generates:**

```javascript
gql`
    query AccountOpportunities($accountId: ID, $first: Int) {
        uiapi {
            query {
                Opportunity(where: { AccountId: { eq: $accountId } }, first: $first) {
                    edges { node { Id { value } Name { value } } }
                }
            }
        }
    }
`
```

The component then infers "has more" from `edges.length === first`, which silently lies when the server filters part of a page.

**Why it happens:** Models often compress connection queries by dropping `pageInfo`, because demo snippets in public GraphQL tutorials frequently do.

**Correct pattern:**

```javascript
gql`
    query AccountOpportunities($accountId: ID, $first: Int, $after: String) {
        uiapi {
            query {
                Opportunity(
                    where: { AccountId: { eq: $accountId } }
                    first: $first
                    after: $after
                ) {
                    edges { node { Id { value } Name { value } } cursor }
                    pageInfo { endCursor hasNextPage }
                }
            }
        }
    }
`
```

**Detection hint:** `edges` appearing inside a `gql` literal without a sibling `pageInfo` in the same connection block. Any connection query intended for pagination must select `pageInfo`.

---

## Anti-Pattern 6: Defaulting To `lightning/uiGraphQLApi` (v1) For New Components

**What the LLM generates:**

```javascript
import { gql, graphql, refreshGraphQL } from 'lightning/uiGraphQLApi';
```

**Why it happens:** The v1 module dominates pre-Winter-'26 training data — blog posts, LWC Recipes snapshots, and Stack Exchange answers — so the model reaches for it reflexively even for brand-new components that will never run Mobile Offline.

**Correct pattern:** default to v2, which the official reference recommends ("We recommend that you use `lightning/graphql` (v2) where possible").

```javascript
import { gql, graphql, executeMutation } from 'lightning/graphql';
// refresh via the emitted result: await this.graphqlResult.refresh();
```

Only choose v1 when the component must run in a Mobile Offline context, which v2 "doesn't currently support."

**Detection hint:** An import from `lightning/uiGraphQLApi` in a new component with no Mobile Offline requirement — especially paired with a request for optional fields, dynamic queries, or GraphQL mutations, none of which v1 supports.
