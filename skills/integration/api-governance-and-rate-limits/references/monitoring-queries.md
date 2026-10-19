# Monitoring Queries and Threshold Arithmetic

## The `/limits` entry you govern on

```bash
sf api request rest "/services/data/v67.0/limits/" --target-org prod \
  | python3 -c "import json,sys; d=json.load(sys.stdin)['DailyApiRequests']; \
                print(d['Max'], d['Remaining'], round(100*(1-d['Remaining']/d['Max']),1), '% used')"
```

`DailyApiRequests` carries `Max` and `Remaining`; used = `Max - Remaining`. Values are accurate within five minutes — poll from one scheduler, not from every worker.

## Attribution: who spent it

Start with the top-consumers query in SKILL.md (`ApiTotalUsageEventLog`, API 61.0+, needs View Event Log Object Data). Then drill into one consumer to see which resources it spends calls on:

```soql
SELECT ApiResource, HttpMethod, COUNT(Id) calls
FROM ApiTotalUsageEventLog
WHERE ConnectedAppIdentifier = '<connected app ID from the first query>'
  AND IsApiLimitCounted = true AND Timestamp = LAST_N_DAYS:1
GROUP BY ApiResource, HttpMethod
ORDER BY COUNT(Id) DESC
LIMIT 20
```

A resource that appears thousands of times with `PATCH` is a row-by-row sync and the first candidate for Bulk API 2.0 or `/composite`.

Requests that did not count (for example, from certain Salesforce connected apps):

```soql
SELECT ApiFamily, COUNT(Id) calls
FROM ApiTotalUsageEventLog
WHERE IsApiLimitCounted = false AND Timestamp = LAST_N_DAYS:1
GROUP BY ApiFamily
```

## Threshold arithmetic

| Org | Allocation | 70% alert | 85% page |
|---|---|---|---|
| Enterprise, 15 Salesforce licences | 100,000 + 15 × 1,000 = 115,000 | 80,500 | 97,750 |
| Unlimited, 200 Salesforce licences | 100,000 + 200 × 5,000 = 1,100,000 | 770,000 | 935,000 |
| Developer Edition | 15,000 | 10,500 | 12,750 |

Add purchased API add-ons to the allocation before computing thresholds. Configure the same percentages in Setup > API Usage Notifications so a human is emailed even if the dashboard job fails.

## Per-consumer quota sheet (fill in)

| Consumer | Connected app | Integration user | Share of allocation | Middleware cap (req/min) | Owner |
|---|---|---|---|---|---|
| Nightly ETL | | | 40% | | |
| Order sync | | | 20% | | |
| Headroom (unassigned) | — | — | 20% | — | Platform team |
