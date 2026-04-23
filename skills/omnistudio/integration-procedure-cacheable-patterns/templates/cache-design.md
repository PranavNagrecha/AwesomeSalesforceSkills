# IP Cache Design

## IP

- Name:
- Current latency (p50 / p95):
- Calls / hour (peak):
- Source data volatility:

## Cache Key

- Prefix (namespace + ip name + version):
- Input fields included:
- Input fields excluded (justify):
- Example key:

## Partition

- [ ] Org-wide (justify)
- [ ] Session (per-user)

## TTL

- Seconds:
- Rationale (source SLA / tolerance for stale):

## Invalidation

- [ ] Event-driven (source object → platform event → Apex purge)
- [ ] Versioned prefix bump
- [ ] Namespace purge on deploy

## Fallback

- On cache null / error: (live fetch path)
- On live fetch error: (error surface / default)

## Monitoring

- Hit ratio target: _%
- Alert on hit ratio < target
- Evictions trend

## Sign-Off

- [ ] Partition matches data scope.
- [ ] Key is versioned and readable.
- [ ] Invalidation wired.
- [ ] Fallback never fails hard.
- [ ] Hit ratio measurable.
