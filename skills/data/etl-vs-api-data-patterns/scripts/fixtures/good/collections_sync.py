import json, urllib.request

def push(records, base, token):
    for start in range(0, len(records), 200):
        chunk = records[start:start + 200]
        body = json.dumps({"allOrNone": False, "records": chunk}).encode()
        req = urllib.request.Request(f"{base}/composite/sobjects/Contact/Commerce_Profile_Id__c", data=body, method="PATCH")
        req.add_header("Authorization", f"Bearer {token}")
        urllib.request.urlopen(req)
