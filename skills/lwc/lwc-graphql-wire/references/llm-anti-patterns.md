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

**Detection hint:** `\$\{` appearing anywhere inside a `gql\`...\`` literal. Any match is almost certainly a bug.

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

**Correct pattern:**

```javascript
import { gql, graphql, refreshGraphQL } from 'lightning/uiGraphQLApi';

async handleSaved() {
    await refreshGraphQL(this.wiredResult);
}
```

**Detection hint:** Any file that imports both `refreshApex` from `@salesforce/apex` and `graphql` from `lightning/uiGraphQLApi`, or any call to `refreshApex` with an argument that was populated by a `graphql` wire handler.

---

## Anti-Pattern 4: Generating A `mutation` Block

**What the LLM generates:**

```javascript
const UPDATE_ACCOUNT = gql`
    mutation UpdateAccount($id: ID!, $name: String!) {
        updateAccount(input: { id: $id, name: $name }) { Id }
    }
`;
```

**Why it happens:** Other GraphQL ecosystems (Apollo, Relay, GitHub, Shopify) all expose mutation support, and the model assumes Salesforce UI API GraphQL mirrors that shape. It does not — the adapter is read-only.

**Correct pattern:**

```javascript
import { updateRecord } from 'lightning/uiRecordApi';
import { gql, graphql, refreshGraphQL } from 'lightning/uiGraphQLApi';

async save() {
    await updateRecord({ fields: { Id: this.recordId, Name: this.newName } });
    await refreshGraphQL(this.wiredResult);
}
```

**Detection hint:** A `gql\`...\`` literal (or `gql(` call) whose contents contain the keyword `mutation`. Any match is wrong on this platform.

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
