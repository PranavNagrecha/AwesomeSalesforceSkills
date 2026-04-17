# Examples — Shield Platform Encryption — BYOK / KMS Setup

## Example 1: BYOK tenant secret upload

**Context:** Healthcare provider, HIPAA.

**Problem:** Using platform-managed keys does not satisfy BAA requirements.

**Solution:**

In AWS KMS generate a 256-bit data key; derive tenant secret per Salesforce BYOK spec; upload via Setup; rotate every 90 days with a runbook.

**Why it works:** Customer retains full key provenance; destroy-key test proves crypto erasure.


---

## Example 2: Cache-Only Key Service with AWS

**Context:** Financial services firm refuses to upload key material.

**Problem:** Latency spike worries.

**Solution:**

Stand up AWS API Gateway + Lambda backed by KMS; configure Salesforce Cache-Only callback; load-test 95p decrypt <40ms with gateway caching at 5 min.

**Why it works:** Key never leaves customer cloud; cache tier absorbs the callback cost.

