// Loads observations into the Healthcare API at api.healthcloud.salesforce.com
const BUNDLE_SIZE = 200;
const concurrency = 20;
const SCOPES = 'patient/*.read system/*.write refresh_token';
export async function send(bundle) {
  const res = await fetch('https://api.healthcloud.salesforce.com/bundle/fhir-r4/v1/Bundle', {
    method: 'POST', body: JSON.stringify(bundle)
  });
  if (res.status >= 400) throw new Error('bundle failed ' + res.status);
  return res.json();
}
