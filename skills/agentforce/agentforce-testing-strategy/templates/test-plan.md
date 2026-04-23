# Agentforce Test Plan

## Coverage Matrix

| Layer | Count | Run Frequency | Owner |
|---|---|---|---|
| Action unit tests |  | per PR |  |
| Routing tests |  | per PR |  |
| Golden prompts |  | per release |  |
| Adversarial |  | nightly |  |
| Prod replay |  | weekly |  |

## Golden Prompt (Per Topic)

- 3-5 cases each covering:
  - happy path
  - ambiguous phrasing
  - off-scope redirect

## Adversarial Buckets

- [ ] Jailbreak
- [ ] PII echo
- [ ] Off-scope
- [ ] Ambiguity
- [ ] Identity spoofing
- [ ] Data exfil via action

## Metrics Dashboard

- [ ] Routing accuracy.
- [ ] Action precision.
- [ ] PII leak count (zero tolerance).
- [ ] Refusal correctness.
- [ ] Tone drift flag.

## Sign-Off

- [ ] No real PII in corpus.
- [ ] Dashboard owned by a named person.
- [ ] Quarterly prune scheduled.
- [ ] Prod replay pipeline sanitises before sampling.
