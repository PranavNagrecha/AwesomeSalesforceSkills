import { LightningElement, wire } from 'lwc';
import { gql, graphql } from 'lightning/uiGraphQLApi';

export default class LegacySearch extends LightningElement {
    searchKey = 'Acme';

    @wire(graphql, { query: '$query' })
    handle({ data, error }) {
        if (error) {
            console.error(error);
        }
    }

    get query() {
        return gql`
            query {
                uiapi { query { Account(first: 5000, where: { Name: { like: "${this.searchKey}%" } }) {
                    edges { node { Id Name { value } } }
                } } }
            }
        `;
    }
}
