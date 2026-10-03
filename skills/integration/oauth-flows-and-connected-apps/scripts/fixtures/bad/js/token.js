export async function token() {
  const body = 'grant_type=client_credentials&scope=api%20refresh_token';
  const legacy = 'grant_type=password&username=svc@example.com';
  return fetch('https://example.my.salesforce.com/services/oauth2/token', { method: 'POST', body });
}
