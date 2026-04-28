import { LightningElement, api, wire } from 'lwc';
import { gql, graphql, refreshGraphQL } from 'lightning/uiGraphQLApi';

/**
 * graphqlWirePattern — canonical multi-entity read via UI API GraphQL.
 *
 * Preferred over multiple `@wire(getRecord)` calls when:
 *  - The UI renders parent + related list in one shot.
 *  - You need a stable cache key for refresh on mutation.
 *  - The field set is small and known at design time.
 *
 * Do NOT use for:
 *  - Writes — GraphQL adapter is read-only. Use `updateRecord` / Apex.
 *  - Single-record reads with no relationships — `getRecord` is cheaper.
 *  - Aggregates or complex joins — drop to Apex + SOQL.
 *
 * Refresh after writes: pass `this.wiredAccount` to `refreshGraphQL`.
 */
export default class GraphqlWirePattern extends LightningElement {
    @api recordId;
    wiredAccount;

    @wire(graphql, {
        query: gql`
            query AccountWithContacts($recordId: ID) {
                uiapi {
                    query {
                        Account(where: { Id: { eq: $recordId } }) {
                            edges {
                                node {
                                    Id
                                    Name { value }
                                    Industry { value }
                                    Contacts(first: 25, orderBy: { LastName: { order: ASC } }) {
                                        edges {
                                            node {
                                                Id
                                                Name { value }
                                                Email { value }
                                            }
                                        }
                                        pageInfo { hasNextPage endCursor }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        `,
        variables: '$queryVariables'
    })
    setWiredAccount(result) {
        this.wiredAccount = result;
    }

    get queryVariables() {
        return { recordId: this.recordId };
    }

    get account() {
        const edges = this.wiredAccount?.data?.uiapi?.query?.Account?.edges;
        return edges?.[0]?.node;
    }

    get contacts() {
        const edges = this.account?.Contacts?.edges ?? [];
        return edges.map(e => e.node);
    }

    get hasError() {
        return !!this.wiredAccount?.errors?.length;
    }

    async refresh() {
        if (this.wiredAccount) {
            await refreshGraphQL(this.wiredAccount);
        }
    }
}
