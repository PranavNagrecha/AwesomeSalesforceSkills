# LLM Anti-Patterns — GraphQL API Patterns

Common mistakes AI coding assistants make when generating or advising on Salesforce GraphQL API usage.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Calling the Salesforce GraphQL API read-only, or treating it as a custom GraphQL server

**What the LLM generates:** Either "Salesforce GraphQL has no mutations, so writes must go through REST", or custom `type` definitions and resolvers as if the org exposed an editable schema.

**Why it happens:** Older material described a query-only API, and generic GraphQL training data covers custom schemas. An earlier version of this file made the first mistake.

**Correct pattern:**

```text
Salesforce GraphQL API facts (GraphQL API Developer Guide, fetched 2026-10-03):
- Endpoint: POST https://{MyDomainName}.my.salesforce.com/services/data/vXX.X/graphql
- Schema is generated from UI API supported objects and honors the user's OLS/FLS
- No custom resolvers or schema extensions
- Mutations: beta v59.0-v65.0, generally available v66.0+; uiapi input allOrNone
  (default true); creating a record with child relationships is not supported
- LWC: lightning/graphql (v2) by default; lightning/uiGraphQLApi (v1) for Mobile
  Offline; the wire adapter supports mutations from v66.0
```

**Detection hint:** Advice that GraphQL cannot write data, or `type Query` / `type Mutation` schema definitions in Salesforce code.

---

## Anti-Pattern 2: Choosing the wrong LWC GraphQL module

**What the LLM generates:** `import { gql, graphql } from 'lightning/uiGraphQLApi';` for a new desktop component, sometimes with a comment that `lightning/graphql` is "incorrect". An earlier version of this file said exactly that.

**Why it happens:** v1 examples predate v2 and dominate older training data.

**Correct pattern:**

```javascript
// Default for new components (LWC guide: v2 supersedes v1)
import { LightningElement, wire, api } from 'lwc';
import { gql, graphql } from 'lightning/graphql';

export default class AccountContacts extends LightningElement {
    @api recordId;

    @wire(graphql, { query: '$contactsQuery', variables: '$variables' })
    result;

    get contactsQuery() {
        if (!this.recordId) return undefined;
        return gql`
            query contactsForAccount($accountId: ID) {
                uiapi {
                    query {
                        Contact(where: { AccountId: { eq: $accountId } }, first: 10) {
                            edges { node { Id Name { value } } }
                        }
                    }
                }
            }
        `;
    }

    get variables() {
        return { accountId: this.recordId };
    }
}
// Use 'lightning/uiGraphQLApi' only when the component must work in Mobile Offline.
```

**Detection hint:** A `lightning/uiGraphQLApi` import in a component whose targets do not include a mobile offline experience.

---

## Anti-Pattern 3: Not Using Connection-Based Pagination

**What the LLM generates:** `query { Account { Id Name } }` without using the connection-based pagination model (edges, node, pageInfo, cursor) that Salesforce's GraphQL API requires for list queries.

**Why it happens:** Simple GraphQL query syntax works on many GraphQL servers. Salesforce uses a Relay-style connection model that requires edges/node wrapping, which is specific to their implementation.

**Correct pattern:**

```graphql
query PaginatedAccounts($cursor: String) {
  uiapi {
    query {
      Account(first: 50, after: $cursor) {
        edges {
          node {
            Id
            Name { value }
          }
          cursor
        }
        pageInfo {
          hasNextPage
          endCursor
        }
        totalCount
      }
    }
  }
}

# Pagination flow:
# 1. First call: omit $cursor (returns first 50)
# 2. Check pageInfo.hasNextPage
# 3. If true: set $cursor = pageInfo.endCursor, repeat
```

**Detection hint:** Flag Salesforce GraphQL queries that do not use `edges`, `node`, or `pageInfo`. Check for flat list queries without connection pagination structure.

---

## Anti-Pattern 4: Accessing Field Values Without the { value } Wrapper

**What the LLM generates:** `node { Name }` expecting a direct string value, when Salesforce GraphQL returns field values wrapped in a `{ value, displayValue }` structure.

**Why it happens:** Standard GraphQL returns field values directly. Salesforce wraps them in a value object for additional metadata (displayValue for picklists, etc.). LLMs apply generic GraphQL field access patterns.

**Correct pattern:**

```graphql
# WRONG — does not return the actual value:
query {
  uiapi {
    query {
      Account(first: 10) {
        edges { node { Name } }
      }
    }
  }
}

# CORRECT — access the value property:
query {
  uiapi {
    query {
      Account(first: 10) {
        edges {
          node {
            Name { value displayValue }
            Industry { value displayValue }
          }
        }
      }
    }
  }
}

# In JavaScript: result.data.uiapi.query.Account.edges[0].node.Name.value
```

**Detection hint:** Flag Salesforce GraphQL queries where field selections do not include `{ value }` or `{ value displayValue }`. Bare field names without the value wrapper will not return usable data.

---

## Anti-Pattern 5: Assuming inaccessible fields come back as null

**What the LLM generates:** Result handling that expects `null` for fields the user cannot read, and a claim that GraphQL "silently returns null" for FLS-restricted fields.

**Why it happens:** Some APIs mask restricted fields. The GraphQL API Developer Guide instead says the schema honors the context user's object and field access, so "two different users can have two different views of the GraphQL schema".

**Correct pattern:**

```text
Salesforce GraphQL security behavior:
- The schema itself differs per user: inaccessible objects and fields are not in it
- A query naming a field outside the user's schema returns an error in `errors`
  (usually with HTTP 200), not a null value
  UNVERIFIED (2026-10-03): the exact error text for an FLS-hidden field is inferred
  from the documented filter-field error "Field 'X' in type 'Y' is undefined"
- lightning/graphql (v2) supports optional fields; v1 does not

Implications for LWC components:
1. Read `errors` as well as `data` on every result
2. Test with each persona's permission sets
3. Keep null-safe access for fields that are genuinely empty
```

**Detection hint:** Code or advice that relies on `null` to detect missing field access, or that never reads `errors`.


---

## Anti-Pattern 6: Paging past 4,000 records with relay cursors only

**What the LLM generates:** An export loop that follows `endCursor` until `hasNextPage` is false and assumes it has every record.

**Why it happens:** Cursor paging looks unbounded in generic GraphQL.

**Correct pattern:** The GraphQL API Developer Guide says relay paging without an upper bound retrieves up to 4,000 records. For more than 200 records, pass `upperBound` (v59.0+) with `first` between 200 and 2,000; from v60.0 a later request can add `upperBound` to an existing paging session.

```graphql
query bigAccounts($after: String) {
  uiapi {
    query {
      Account(first: 2000, after: $after, upperBound: 10000) {
        edges { node { Id Name { value } } }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
```

**Detection hint:** A cursor loop over a large object with no `upperBound` argument.

---

## Anti-Pattern 7: Interpolating runtime values into `gql`

**What the LLM generates:**

```javascript
get query() {
    return gql`query { uiapi { query { Account(where: { Name: { like: "${this.searchKey}%" } }) { edges { node { Id } } } } } }`;
}
```

**Why it happens:** Template literals make interpolation look natural.

**Correct pattern:** `gql` is not reactive in either module, and `lightning/uiGraphQLApi` does not support `${}` interpolation at all. Declare a variable and supply it through a `variables` getter:

```javascript
get query() {
    return gql`query accountSearch($name: String) {
        uiapi { query { Account(where: { Name: { like: $name } }) { edges { node { Id } } } } }
    }`;
}
get variables() {
    return { name: `${this.searchKey}%` };
}
```

**Detection hint:** `${` inside a `gql` template that references component state rather than a fragment constant.
