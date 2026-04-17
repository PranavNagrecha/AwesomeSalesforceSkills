# Examples — Pipeline Secrets Management

## Example 1: GitHub Actions JWT step

**Context:** Deploy workflow

**Problem:** Previous config used auth URL

**Solution:**

```yaml
- run: |
    echo "$SF_JWT_KEY" | base64 -d > /tmp/key.pem
    sf org login jwt --client-id $SF_CLIENT_ID --jwt-key-file /tmp/key.pem --username $SF_USERNAME --alias prod
    rm /tmp/key.pem
```

**Why it works:** Key lives only in tmpfs for seconds


---

## Example 2: Rotation job

**Context:** 90-day rotation SLA

**Problem:** Manual rotation missed

**Solution:**

Scheduled GH Action that generates new keypair, uploads cert via Tooling API, updates repo secret via `gh secret set`

**Why it works:** Automated rotation prevents expiration surprises

