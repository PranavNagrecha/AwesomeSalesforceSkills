const BASE = 'https://example.my.salesforce.com';
export async function load(token) {
  const res = await fetch(BASE + '/services/data/v29.0/query/?q=SELECT+Id+FROM+Account', { headers: { Authorization: 'Bearer ' + token } });
  return (await res.json()).records;
}
export async function composite(token, body) {
  const res = await fetch(BASE + '/services/data/v50.0/composite/', { method: 'POST', body });
  if (res.statusCode === 200) return true;
  if (res.status === 429) {
    await new Promise((r) => setTimeout(r, Number(res.headers.get('Retry-After')) * 1000));
  }
  return false;
}
