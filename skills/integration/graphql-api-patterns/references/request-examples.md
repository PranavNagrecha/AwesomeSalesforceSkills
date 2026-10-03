# Request Examples: Paginated LWC Component, Server Request, and Mutation

A deployable Lightning web component that reads related contacts through `lightning/graphql` with cursor paging and error handling, then the raw HTTP forms for a server integration. Query syntax (`where`, `orderBy`, `first`, `after`, `pageInfo`), the request body shape, and the mutation shapes come from the GraphQL API Developer Guide pages fetched 2026-10-03; the wire configuration (`query`, `variables`, `operationName`, `errors`) comes from the LWC Developer Guide `lightning/graphql` reference.

## File: `force-app/main/default/lwc/accountContactsGraphql/accountContactsGraphql.js`

```javascript
import { LightningElement, api, wire } from 'lwc';
import { gql, graphql } from 'lightning/graphql';

const PAGE_SIZE = 10;

export default class AccountContactsGraphql extends LightningElement {
    @api recordId;
    after;
    contacts = [];
    pageInfo;
    errorText;

    @wire(graphql, { query: '$query', variables: '$variables', operationName: 'contactsForAccount' })
    handleResult({ data, errors }) {
        if (errors) {
            this.errorText = errors.map((e) => e.message).join('; ');
            return;
        }
        if (data) {
            const connection = data.uiapi.query.Contact;
            const page = connection.edges.map((edge) => edge.node);
            this.contacts = this.after ? [...this.contacts, ...page] : page;
            this.pageInfo = connection.pageInfo;
            this.errorText = undefined;
        }
    }

    // Returning undefined until recordId exists delays the query.
    get query() {
        if (!this.recordId) {
            return undefined;
        }
        return gql`
            query contactsForAccount($accountId: ID, $first: Int, $after: String) {
                uiapi {
                    query {
                        Contact(
                            where: { AccountId: { eq: $accountId } }
                            first: $first
                            after: $after
                            orderBy: { LastName: { order: ASC } }
                        ) {
                            edges {
                                node {
                                    Id
                                    Name { value }
                                }
                            }
                            pageInfo {
                                hasNextPage
                                endCursor
                            }
                        }
                    }
                }
            }
        `;
    }

    get variables() {
        return { accountId: this.recordId, first: PAGE_SIZE, after: this.after || null };
    }

    get hasMore() {
        return Boolean(this.pageInfo && this.pageInfo.hasNextPage);
    }

    loadMore() {
        this.after = this.pageInfo.endCursor;
    }
}
```

## File: `force-app/main/default/lwc/accountContactsGraphql/accountContactsGraphql.html`

```html
<template>
    <lightning-card title="Contacts" icon-name="standard:contact">
        <ul class="slds-p-horizontal_medium">
            <template for:each={contacts} for:item="contact">
                <li key={contact.Id}>{contact.Name.value}</li>
            </template>
        </ul>
        <template lwc:if={hasMore}>
            <div class="slds-p-around_medium">
                <lightning-button label="Load more" onclick={loadMore}></lightning-button>
            </div>
        </template>
        <template lwc:if={errorText}>
            <p class="slds-text-color_error slds-p-horizontal_medium">{errorText}</p>
        </template>
    </lightning-card>
</template>
```

## File: `force-app/main/default/lwc/accountContactsGraphql/accountContactsGraphql.js-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>lightning__RecordPage</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="lightning__RecordPage">
            <objects>
                <object>Account</object>
            </objects>
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

Design notes:

| Choice | Reason |
|---|---|
| `lightning/graphql` | v2 supersedes v1; v1 only for Mobile Offline |
| Runtime values in `variables` | `gql` is not reactive; the getter re-runs the wire when values change |
| `operationName` and a named query | The LWC guide recommends naming operations for server-side debugging |
| `first: 10` with `after` | Relay paging; for lists that can pass 4,000 rows, switch to `upperBound` |
| `errors` handled before `data` | The wire uses `errors` (plural), and GraphQL can return both |

UNVERIFIED (2026-10-03): accumulating pages by changing the `after` variable re-runs the wire with a new cache key; the GraphQL guide's pagination pages for the wire adapter were not read in full, so confirm the refresh behavior in a sandbox.

## Manifest: `manifest/package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>accountContactsGraphql</members>
        <name>LightningComponentBundle</name>
    </types>
    <version>67.0</version>
</Package>
```

## Request: server integration query

```bash
curl --request POST 'https://MyDomainName.my.salesforce.com/services/data/v67.0/graphql' \
  -H 'Authorization: Bearer <access token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "query accountById($id: ID) { uiapi { query { Account(where: { Id: { eq: $id } }) { edges { node { Id Name { value } } } } } } }",
    "operationName": "accountById",
    "variables": { "id": "001xx000003GYQxAA0" }
  }'
```

A validation failure still returns HTTP 200, with the detail in `errors`:

```json
{
  "data": {},
  "errors": [
    {
      "extensions": { "ErrorType": "ValidationError" },
      "locations": [ { "column": 7, "line": 4 } ],
      "message": "Validation error of type FieldUndefined: Field 'Accounts' in type 'RecordQuery' is undefined @ 'uiapi/query/Accounts'",
      "paths": []
    }
  ],
  "extensions": {}
}
```

The guide's own curl samples use `MyDomainName.my.salesforce.com`; the `lightning.force.com` host is not supported for OAuth.

## Request: mutation with explicit transaction behavior (API v66.0+)

```graphql
mutation createTwoAccounts {
  uiapi(input: { allOrNone: false }) {
    first: AccountCreate(input: { Account: { Name: "Trailblazer Express" } }) {
      Record { Id Name { value } }
    }
    second: AccountCreate(input: { Account: { Name: "Amazing Account" } }) {
      Record { Id Name { value } }
    }
  }
}
```

With `allOrNone: false`, a failed create returns `null` for its alias and an entry in `errors` while the other create commits. With the default `allOrNone: true`, every operation rolls back and the others report "The transaction was rolled back since another operation in the same transaction failed." Creating a record together with child relationships is not supported; create the parent, then reference it with `@{alias}` in a later operation.
