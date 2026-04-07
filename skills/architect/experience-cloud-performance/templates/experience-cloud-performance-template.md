# Experience Cloud Performance — Optimization Checklist Template

Use this template when auditing or improving the performance of an Experience Cloud site.
Complete each section before marking performance work done.

## Site Context

**Skill:** `experience-cloud-performance`

**Site name:**
**Template type:** [ ] LWR (Build Your Own)   [ ] Aura
**Custom domain configured:** [ ] Yes   [ ] No
**CDN status (Settings > General):** [ ] Active   [ ] Not active   [ ] Unknown
**Browser caching (Settings > Performance):** [ ] Enabled   [ ] Disabled   [ ] Unknown
**Primary use case:** (e.g., customer self-service portal, partner community, public microsite)
**Peak traffic window:**
**Current known performance symptoms:**

---

## Phase 1: Configuration Audit

Work through these before looking at code. Many performance issues are configuration, not code.

### CDN and Caching Settings

- [ ] Custom domain is configured in production org (`Setup > Custom URLs`)
- [ ] CDN toggle is ON in `Experience Builder > Settings > General`
- [ ] Browser caching toggle is ON in `Experience Builder > Settings > Performance`
- [ ] Site has been republished since browser caching was enabled (required for setting to take effect)

**Notes:**

---

### Static Asset Review

| Asset Type | Reference URL Pattern | Version Token Present? | Action Required |
|---|---|---|---|
| Static resource | `/resource/...` | [ ] Yes [ ] No | |
| Content asset | `@salesforce/contentAsset/...` | [ ] Yes [ ] No | |
| Org image / logo | | [ ] Yes [ ] No | |

**Static resources without version tokens must be renamed and re-referenced to force cache invalidation on update (1-day CDN TTL applies).**

---

## Phase 2: Page Composition Audit

Audit the highest-traffic pages for component weight and Apex call count.

### Page Inventory

| Page Name | Component Count | Apex Wire Call Count | Below-Fold Components | Priority |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |

### Apex Wire Call Detail (Top 3 Priority Pages)

**Page:**

| Component | Apex Method Called | cacheable=true? | Can Consolidate? |
|---|---|---|---|
| | | [ ] Yes [ ] No | [ ] Yes [ ] No |
| | | [ ] Yes [ ] No | [ ] Yes [ ] No |
| | | [ ] Yes [ ] No | [ ] Yes [ ] No |

**Consolidation plan:** (describe the wrapper class / data provider approach if applicable)

---

## Phase 3: LWR-Specific Checks

Skip this section for Aura sites.

- [ ] Team understands the 60-second CDN HTML TTL after publish (stale window is expected behavior)
- [ ] Team understands the 5-minute permissions module TTL (permission changes take up to 5 minutes)
- [ ] Post-publish validation procedure is documented: wait 90s, validate in incognito, then notify stakeholders
- [ ] Publish schedule avoids peak traffic windows where possible
- [ ] Framework JS/CSS bundles are generated at publish time with versioned URLs (no manual action required — confirm this is working by checking that URLs include a version key)

**LWR Publish Procedure (for operations runbook):**
```
1. Publish site in Experience Builder
2. Wait 90 seconds
3. Open incognito window, navigate to site
4. Verify expected changes are visible
5. Notify stakeholders
```

---

## Phase 4: Component Loading Optimization

- [ ] Below-the-fold components on high-traffic pages use deferred initialization (conditional render on scroll/interaction)
- [ ] Apex methods used as wire targets are marked `cacheable=true` where the data is read-only
- [ ] Data provider pattern implemented for pages with 4+ original wire calls
- [ ] Third-party scripts loaded asynchronously (script tags use `async` or `defer` in Head Markup)
- [ ] Images use appropriate dimensions and are not over-sized for their display context

**Components identified for deferred loading:**

| Page | Component | Estimated Position | Deferred? |
|---|---|---|---|
| | | Below fold | [ ] Yes [ ] No |
| | | Below fold | [ ] Yes [ ] No |

---

## Phase 5: Validation

- [ ] Browser Network tab checked: Apex call count matches expected post-optimization count
- [ ] Browser Network tab checked: static assets are returning 304 (cached) on repeat page loads
- [ ] Performance validated on mobile connection simulation (Chrome DevTools > Network throttling > Fast 3G)
- [ ] Post-publish stale window documented and communicated to site operations team
- [ ] LWR permissions TTL behavior documented for support team

---

## Decisions and Deviations

Record any decisions made during this optimization work and why deviations from the standard approach were accepted.

| Decision | Reason | Owner |
|---|---|---|
| | | |
| | | |

---

## Sign-off

- [ ] All Phase 1 configuration settings confirmed and documented
- [ ] High-traffic pages audited (Phase 2)
- [ ] LWR-specific operational procedures documented (Phase 3)
- [ ] Component loading optimization implemented and validated (Phase 4 + 5)
- [ ] Findings summarized for project record

**Completed by:**
**Date:**
