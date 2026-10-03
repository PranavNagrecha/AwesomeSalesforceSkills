import requests

BASE = "https://example.my.salesforce.com"
VERSION = "v67.0"


def query_all(token, soql):
    url = f"/services/data/{VERSION}/query/?q={soql}"
    rows = []
    while url:
        page = requests.get(BASE + url, headers={"Authorization": f"Bearer {token}"}).json()
        rows.extend(page["records"])
        url = None if page["done"] else page["nextRecordsUrl"]
    return rows


def send_composite(token, payload):
    resp = requests.post(f"{BASE}/services/data/{VERSION}/composite/", json=payload,
                         headers={"Authorization": f"Bearer {token}"})
    if resp.status_code == 403 and any(e.get("errorCode") == "REQUEST_LIMIT_EXCEEDED" for e in resp.json()):
        raise RuntimeError("API allocation exhausted")
    failures = [r for r in resp.json()["compositeResponse"] if r["httpStatusCode"] >= 400]
    return failures
