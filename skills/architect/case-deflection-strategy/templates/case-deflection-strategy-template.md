# Case Deflection Strategy — Work Template

Use this template when designing or assessing a case deflection program.

## Scope

**Skill:** `case-deflection-strategy`

**Request summary:** (fill in what the user asked for — e.g., "Design a deflection program to reduce chat volume by 25%")

---

## 1. Contact Volume Analysis

| Contact Reason / Topic | Channel | Monthly Volume | % of Total | Complexity (Low/Med/High) | Deflection Candidate? |
|---|---|---|---|---|---|
| (from ECM or case report) | | | | | |
| | | | | | |
| | | | | | |

**ECM data available?** Yes / No
**Transcript history available:** __ months
**If no ECM:** describe substitute analysis method used:

---

## 2. Knowledge Readiness Assessment

| Deflection Topic | Article Exists? | Customer-Readable? | Data Categories Assigned? | Visible on Target Channel? | Action Required |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |

**Knowledge readiness gate:** If fewer than 70% of wave 1 topics have compliant articles, defer channel launch and run knowledge sprint first.

---

## 3. Channel Selection

| Topic | Recommended Channel | Rationale |
|---|---|---|
| (informational) | Knowledge search-first portal | Answerable by article; no transaction needed |
| (transactional) | Einstein Bot + Flow automation | Requires system action; API callout or Flow |
| (complex) | Agent queue (no deflection) | Requires human judgment; deflection not appropriate |

**Primary deflection channel selected:** (Einstein Bot / Experience Cloud portal search-first / Both)

---

## 4. KPI Framework

**Baseline (before launch):**
- Total inbound volume (channel): __ contacts/month
- Current case creation rate (if web channel): __ cases/month
- Average agent handle time for deflection target topics: __ minutes

**Targets:**
- Deflection rate target: __%
  (Calibration: wave 1 topics represent __% of total volume; set target at 50–70% of that)
- Goal completion rate (GCR) target: __% (aim for 55%+)
- Containment rate target (bot deployments): __%
- Post-deflection case creation rate ceiling: __%

**KPI definitions agreed with stakeholders:**
- [ ] Deflection rate formula documented and agreed
- [ ] GCR measurement method confirmed (survey / behavioral signal / both)
- [ ] Reporting cadence set: __ (weekly / monthly)

---

## 5. Data Category Audit

| Data Category Group | Child Categories in Use | Guest User Visibility Set? | Authenticated User Visibility Set? | Articles Assigned Correctly? |
|---|---|---|---|---|
| | | | | |

**Test plan:** Verify article visibility as guest user via Experience Cloud site preview before launch.

---

## 6. Wave Rollout Plan

| Wave | Topics | Channel | Knowledge Status | Target Launch Date | GCR Target |
|---|---|---|---|---|---|
| Wave 1 | (3–5 top topics by volume) | | | | |
| Wave 2 | (next 5 topics) | | | | |
| ECM refresh | — | — | — | (60 days post-Wave 1) | — |

---

## 7. Review Checklist

Copy from SKILL.md and mark as complete:

- [ ] ECM report or equivalent topic analysis completed with at least 10 topics ranked by volume
- [ ] Each deflection candidate topic mapped to informational / transactional / complex
- [ ] Knowledge article coverage assessed against deflection candidate list; gaps documented
- [ ] Data category assignments validated for target channel and user profile (guest and/or authenticated)
- [ ] KPI framework defined: deflection rate baseline, GCR target, containment rate target (bot deployments)
- [ ] Bot or portal deflection channel configured with per-topic session tagging for reporting
- [ ] Post-launch review scheduled within 30 days with ECM re-run planned at 60 days

---

## Notes

Record any deviations from the standard pattern and why:
