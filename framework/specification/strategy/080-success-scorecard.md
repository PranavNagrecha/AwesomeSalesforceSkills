# Success scorecard

## Product value

| Measure | Definition | Release use |
|---|---|---|
| Time to first useful finding | Invocation to first accepted material finding | Compare against raw/vanilla workflow |
| Required-finding recall | Required known-truth findings present with valid evidence | Primary behavioral outcome |
| Root-cause rank | Correct cause in top 1/top 3 | Triage usefulness |
| Recommendation acceptance | User accepts/removes/changes proposed next action | Real-world utility |
| Resolution contribution | Run materially helped resolve/plan the job | North-star input |

## Trust and safety

| Measure | Goal |
|---|---:|
| Material evidence-reference validity | >=98% release minimum |
| Accepted unsupported material claims | 0 in release scenario set |
| Prohibited Salesforce product mutations | 0 |
| Secret disclosure | 0 |
| Wrong target selection | 0 |
| Hard status error on unsafe/missing evidence case | 0 |
| Independent reviewer escape rate | measured and reduced |

## Context and system quality

- knowledge/reference files selected;
- estimated and actual tokens where available;
- raw versus normalized tool bytes;
- truncation and pagination;
- compaction/resume success;
- second-task contamination;
- stage duration and tool retries;
- host capability/enforcement gaps.

## Adoption

- install attempts and doctor pass;
- fixture activation within fifteen minutes;
- first real job;
- second run within fourteen days;
- weekly active after eight weeks;
- products used per retained user;
- replay/share/contribution rate;
- uninstall and stated reason.

## Reporting rules

Every benchmark number includes:

- product/scenario dataset version;
- sample size and inclusion rules;
- host, model, Salesforce, CLI/MCP, and framework versions;
- run date and environment;
- scoring method and human-review process;
- failures, excluded runs, and uncertainty;
- baseline definition.

Do not combine incomparable products into one “accuracy” score.
