const query = 'query { uiapi { query { Account(first: 100, upperBound: 10000) { edges { node { Id } } } } } }';
export async function run(token) {
  return fetch('https://acme.lightning.force.com/services/data/v67.0/graphql', {
    method: 'POST',
    headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
  });
}
