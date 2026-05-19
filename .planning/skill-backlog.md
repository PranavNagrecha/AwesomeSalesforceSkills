# Deferred Skill Candidates

Candidates that passed the gap-verification bar but were deferred because
the scheduled-task run had already accepted a skill and the brief cap is
3 per run / quality over quota.

Deferred candidates are NOT scaffolded; the next scheduled run should
re-verify against current state (catalog may have grown) before scaffolding.

---

## 2026-05-19

### `admin/related-list-configuration`

**Verified phrasings:**

- `related list enhanced configuration quick related list page layout assignment columns`
  → top hit `admin/fsl-sla-configuration-requirements` 3.092 (FSL-specific —
  WorkOrderMilestone on Work Order layouts; orthogonal to general related-list
  config).
- `related list filtering sorting view all configure related records page`
  → top hit `admin/lightning-page-performance-tuning` 2.752 (covers
  Related List - Single vs Full **performance** profile only, not general
  configuration).

**Articulated delta:** Both existing hits touch related lists incidentally
(FSL milestones; Lightning page performance). Neither focuses on the
day-to-day admin task of configuring related lists on page layouts:
column choice (max 10), sort field selection, filtering (Spring '24
Enhanced Related Lists), Related List - Single vs Related Lists -
Standard component choice in Lightning App Builder, the "View All" UX,
and per-record-type related-list assignment quirks.

**Reason deferred:** Run already shipped `admin/global-search-configuration`.
Borderline candidate — staying conservative per brief ("Quality > quota").

**Re-verify next run:** Yes. Phrasings to re-run:
1. `related list enhanced configuration quick related list page layout assignment columns`
2. `related list filtering sorting view all configure related records page`
3. `Enhanced Related Lists Spring 24 filter sort related records`
