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
