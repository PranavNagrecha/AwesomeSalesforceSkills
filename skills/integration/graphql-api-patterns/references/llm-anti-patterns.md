# LLM Anti-Patterns — GraphQL API Patterns

Common mistakes AI coding assistants make when generating or advising on Salesforce GraphQL API usage.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Confusing Salesforce GraphQL API with Generic GraphQL

**What the LLM generates:** GraphQL mutations, custom resolvers, or schema definitions as if Salesforce exposes a fully customizable GraphQL server. Salesforce's GraphQL API is read-only (queries only, no mutations in the standard API) and has a fixed schema derived from the org's metadata.

**Why it happens:** General GraphQL training data covers full CRUD operations, custom schemas, and mutations. Salesforce's GraphQL API is a read-only query surface over sObjects, not a generic GraphQL endpoint.

**Correct pattern:**

```text
Salesforce GraphQL API constraints:
- Read-only: queries only, NO mutations (as of Spring '25)
- Schema is auto-generated from org metadata (objects, fields, relationships)
- No custom resolvers or schema extensions
- Two endpoints:
  1. /services/data/vXX.0/graphql (external REST-based GraphQL)
  2. @wire(graphql) in LWC via lightning/uiGraphQLApi (internal LWC wire)

For write operations, use:
- REST API (CRUD on sObjects)
- Composite API (multi-step operations)
- Apex @AuraEnabled methods (from LWC)
```

**Detection hint:** Flag GraphQL examples containing `mutation`, `type Mutation`, or custom `type` definitions in Salesforce context. These are not supported.

---

## Anti-Pattern 2: Using the Wrong GraphQL Wire Adapter Import in LWC

**What the LLM generates:** `import { graphql } from 'lightning/graphql'` or other incorrect import paths instead of the correct `lightning/uiGraphQLApi` module.

**Why it happens:** LLMs generate import paths from generic LWC patterns or incorrect module names. The actual module name (`lightning/uiGraphQLApi`) is specific and less common in training data.

**Correct pattern:**

```javascript
// Correct import for LWC GraphQL wire adapter:
import { gql, graphql } from 'lightning/uiGraphQLApi';

// Usage in LWC:
export default class MyComponent extends LightningElement {
    @wire(graphql, { query: '$accountQuery', variables: '$variables' })
    graphqlResult;

    get accountQuery() {
        return gql`
            query AccountQuery($accountId: ID!) {
                uiapi {
                    query {
                        Account(where: { Id: { eq: $accountId } }) {
                            edges {
                                node {
                                    Id
                                    Name { value }
                                    Industry { value }
                                }
                            }
                        }
                    }
                }
            }
        `;
    }
}
```

**Detection hint:** Flag LWC imports from `lightning/graphql`, `@salesforce/graphql`, or `graphql` without the `lightning/uiGraphQLApi` module. Check for incorrect module paths.

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

## Anti-Pattern 5: Not Accounting for FLS and CRUD in GraphQL Results

**What the LLM generates:** GraphQL queries assuming all fields will return data without noting that Salesforce's GraphQL API respects Field-Level Security (FLS) and CRUD permissions — fields the user cannot access return null without an error.

**Why it happens:** Generic GraphQL APIs return errors for unauthorized field access. Salesforce's GraphQL API silently returns null for FLS-restricted fields, which is a Salesforce-specific behavior.

**Correct pattern:**

```text
Salesforce GraphQL security behavior:
- Respects the running user's profile/permission set FLS
- Fields the user cannot read: return null (NO error thrown)
- Objects the user cannot access: return empty edges (NO error thrown)
- This is different from REST API, which also respects FLS but may
  return different error shapes

Implications for LWC components:
1. Always handle null values in component template:
   {account.Name?.value ?? 'No Access'}
2. Do not assume all fields will return data
3. Test with restricted user profiles to verify behavior
4. Use @wire error handling for authentication/authorization failures
```

**Detection hint:** Flag GraphQL result handling code that does not check for null field values. Look for direct `.value` access without null-safe operators.
