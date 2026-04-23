# Examples — LWC GraphQL Wire

## Example 1: Parent Account Plus Related Contacts In One Query

**Context:** An Account detail component was running three wires — `getRecord` for the Account, `getListRecords` for child Contacts, and another `getRecord` for the Account Owner — and the payload included fields no one rendered. Switching to a single GraphQL query collapses the three requests into one and lets LDS share the cache across the page.

**Problem:** Three wires mean three provisioning lifecycles, three refresh handles, and independent rerenders when any one of them resolves. Coordinating refresh after an imperative update becomes fragile.

**Solution:**

```javascript
import { LightningElement, api, wire } from 'lwc';
import { gql, graphql, refreshGraphQL } from 'lightning/uiGraphQLApi';

export default class AccountOverview extends LightningElement {
    @api recordId;
    wiredResult;

    // Stable identity — only changes when recordId changes.
    get variables() {
        return { accountId: this.recordId, first: 10 };
    }

    @wire(graphql, {
        query: gql`
            query AccountWithContacts($accountId: ID, $first: Int) {
                uiapi {
                    query {
                        Account(where: { Id: { eq: $accountId } }, first: 1) {
                            edges {
                                node {
                                    Id
                                    Name { value }
                                    Industry { value displayValue }
                                    Owner { Name { value } }
                                    Contacts(first: $first, orderBy: { LastName: { order: ASC } }) {
                                        edges {
                                            node {
                                                Id
                                                Name { value }
                                                Email { value }
                                                Title { value }
                                            }
                                        }
                                        totalCount
                                    }
                                }
                            }
                        }
                    }
                }
            }
        `,
        variables: '$variables',
        operationName: 'AccountWithContacts'
    })
    handleResult(result) {
        this.wiredResult = result;
    }

    get account() {
        return this.wiredResult?.data?.uiapi?.query?.Account?.edges?.[0]?.node;
    }

    get contacts() {
        return this.account?.Contacts?.edges?.map((e) => e.node) ?? [];
    }

    async refresh() {
        await refreshGraphQL(this.wiredResult);
    }
}
```

**Why it works:** One query, one cache entry, one refresh handle. Template reads use `.value` or `.displayValue` so the rendered output matches what the user expects. `operationName` makes server-side telemetry readable. The `variables` getter returns a stable-identity object until `recordId` actually changes, so the adapter de-dupes across rerenders.

---

## Example 2: Cursor Pagination With "Load More"

**Context:** A related-opportunities panel should show 25 rows initially and let the user reveal more without losing already-rendered rows.

**Problem:** Each wire fire replaces `data`. If the component rebinds the template list to `edges` directly, earlier pages disappear when the cursor advances.

**Solution:**

```javascript
import { LightningElement, api, track, wire } from 'lwc';
import { gql, graphql } from 'lightning/uiGraphQLApi';

export default class OpportunityFeed extends LightningElement {
    @api accountId;
    @track rows = [];
    cursor = null;
    hasNextPage = false;
    wiredResult;

    get variables() {
        return { accountId: this.accountId, first: 25, after: this.cursor };
    }

    @wire(graphql, {
        query: gql`
            query AccountOpportunities($accountId: ID, $first: Int, $after: String) {
                uiapi {
                    query {
                        Opportunity(
                            where: { AccountId: { eq: $accountId } }
                            first: $first
                            after: $after
                            orderBy: { CloseDate: { order: DESC } }
                        ) {
                            edges {
                                node {
                                    Id { value }
                                    Name { value }
                                    Amount { value displayValue }
                                    StageName { value }
                                    CloseDate { value displayValue }
                                }
                                cursor
                            }
                            pageInfo {
                                endCursor
                                hasNextPage
                            }
                        }
                    }
                }
            }
        `,
        variables: '$variables',
        operationName: 'AccountOpportunities'
    })
    handleResult(result) {
        this.wiredResult = result;
        const conn = result?.data?.uiapi?.query?.Opportunity;
        if (!conn) return;
        const newRows = conn.edges.map((e) => e.node);
        // Dedupe by stable id.value when appending — prevents accidental duplicates on refresh.
        const seen = new Set(this.rows.map((r) => r.Id.value));
        this.rows = [...this.rows, ...newRows.filter((n) => !seen.has(n.Id.value))];
        this.hasNextPage = conn.pageInfo?.hasNextPage ?? false;
    }

    loadMore() {
        const endCursor = this.wiredResult?.data?.uiapi?.query?.Opportunity?.pageInfo?.endCursor;
        if (endCursor && this.hasNextPage) {
            this.cursor = endCursor;
        }
    }
}
```

**Why it works:** The accumulator is keyed by `Id.value`, so double-fires never duplicate rows. The `hasNextPage` flag comes from the server, not a client-side length heuristic, so filters that shrink a page do not falsely terminate pagination.

---

## Anti-Pattern: Using GraphQL Wire For A Single Known-Id Record

**What practitioners do:** Reach for GraphQL by default because "one adapter for everything" feels consistent, and write a `gql` query for a single record whose id is already in scope.

**What goes wrong:** `@wire(getRecord, { recordId: '$recordId', fields: [...] })` from `lightning/uiRecordApi` is smaller, cache-hits across record-form components on the same page, and has zero query-parsing cost. A GraphQL query for one record incurs query-plan work, still wraps every scalar in `{ value, displayValue }`, and does not compose with record-edit-form caching the way `getRecord` does.

**Correct approach:** Reserve GraphQL wire for multi-entity reads and cursor-paginated related lists. For `recordId`-based single-record reads, use `getRecord`. If the component starts out as one record and grows into multiple related entities, migrate the whole read path to GraphQL at that point rather than mixing adapters for the same record.
