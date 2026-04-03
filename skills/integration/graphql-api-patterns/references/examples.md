# Examples - Graphql Api Patterns

## Example 1: `lightning/graphql` With Variables

**Context:** An account search component needs a lightweight read model with only a few display fields.

**Problem:** Separate REST calls or broad UI API wire usage create extra payload and client stitching.

**Solution:**

```javascript
import { gql, graphql } from 'lightning/graphql';

const ACCOUNT_QUERY = gql`
  query accountSearch($name: String!) {
    uiapi {
      query {
        Account(first: 10, where: { Name: { like: $name } }) {
          edges {
            node {
              Id
              Name { value }
            }
          }
        }
      }
    }
  }
`;
```

**Why it works:** The request stays stable and the response includes only the fields the component needs.

---

## Example 2: GraphQL For Reads, REST For Commands

**Context:** A portal page needs a shaped case dashboard and also a reassign action.

**Problem:** Teams want to force both reads and writes through GraphQL even though the command path is operational.

**Solution:** Use GraphQL to read the dashboard view model and keep the reassign action on an explicit REST or Apex endpoint.

**Why it works:** Reads stay flexible while commands remain easier to authorize, trace, and evolve.

---

## Anti-Pattern: Interpolated Query Strings

**What practitioners do:** They build the GraphQL document with user input via string concatenation or template interpolation.

**What goes wrong:** Safety, maintainability, and cache behavior all get worse.

**Correct approach:** Keep the document static and push runtime values through variables.
