# Salesforce Object Queryability — Diagnosis Worksheet

One worksheet per failed query. Fill it top to bottom; do not skip to the verdict.
The finished worksheet converts one-for-one into the verdict record in
`references/metadata-examples.md` block 6, which
`scripts/check_salesforce_object_queryability.py` lints.

---

## 1. The failure, verbatim

| Field | Value |
|---|---|
| Object (exactly as written in the query) | |
| Full query string | |
| Surface | `rest-data` / `rest-tooling` / `soap` / `apex` / `bulk` |
| API version used by the client | |
| Running user (username or "system context") | |
| HTTP status | |
| `errorCode` from the response body | |
| `message` from the response body | |

If any row above is blank, stop and re-run the call capturing the full response.
A verdict built on a truncated error is the incident this skill exists to prevent.

---

## 2. Answers to the questions in SKILL.md

| Question | Answer |
|---|---|
| Which surface issued the call, and is that the surface that owns the object? | |
| Was this ever observed working — same org, same user, same version? | |
| Is the org's newest API version above the client's pinned version? | |
| Which user ran it, and does an admin get a different result? | |
| Which installed-package namespaces exist in this org? | |
| Does the caller need rows, or only to know whether rows exist? | |

---

## 3. The six probes

Run in order. Stop at the first `fail` that determines the verdict, but record a
result for all six — `skip` is a legitimate result and must carry a reason.

| # | Check name | Result | Evidence (payload, guide line, or command output) |
|---|---|---|---|
| 1 | `org_api_enabled` | pass / fail / skip | |
| 2 | `in_describe_global` | pass / fail / skip | |
| 3 | `object_queryable` | pass / fail / skip | |
| 4 | `object_accessible` | pass / fail / skip | |
| 5 | `field_accessible` | pass / fail / skip | |
| 6 | `query_executed` | pass / fail / skip | |

Probe commands are in `references/metadata-examples.md` block 1 (REST) and
block 2 (Apex).

---

## 4. Verdict

Exactly one value from the closed vocabulary. Free text here is the defect.

| Verdict | Choose when |
|---|---|
| `object-does-not-exist` | Name absent from Describe Global at the org's newest version, no namespace match, no feature gate |
| `edition-or-feature-gated` | Name absent, and the edition or feature check in block 4 explains why |
| `permission-denied` | Name present and queryable, object access check failed |
| `field-not-visible` | Object access passed; a field in the projection or filter is the failure |
| `namespace-prefix-missing` | A prefixed variant of the name is present in the org |
| `api-version-too-old` | Name absent at the pinned version, present at the org's newest |
| `not-queryable-on-this-surface` | Name present, `queryable: false` — no `query()` call on this object |
| `queryable` | The query ran; zero rows counts as success |

**Verdict:** ______________________

---

## 5. Evidence lines

At least one line each for: what the payload said, what the guide says, and what
the caller should do next. These become the `evidence:` list in the record.

1.
2.
3.

---

## 6. Remediation and hand-off

| Item | Value |
|---|---|
| Action taken (fix query / bump version / grant permission / subquery from parent / abort) | |
| If a permission grant: which permission, and the Object Reference rule that names it | |
| Confidence in this verdict (HIGH / MEDIUM / LOW) | |
| What would change the verdict | |
| Dimension recorded as compared or skipped in the caller's output envelope | |

---

## 7. Before you hand it back

- [ ] Every one of the six probes has a result and evidence.
- [ ] The verdict is one of the eight values, not a sentence.
- [ ] The verdict agrees with the probes (e.g. `object-does-not-exist` requires
      `in_describe_global` = fail).
- [ ] Zero rows was recorded as a success, not a skip.
- [ ] The record lints clean:
      `python3 scripts/check_salesforce_object_queryability.py verdicts/<object>.verdict.yaml`
