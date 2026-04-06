# Metadata Coverage and Dependencies — Work Template

Use this template when assessing metadata coverage or mapping component dependencies.

## Scope

**Skill:** `metadata-coverage-and-dependencies`

**Request summary:** (fill in what the user asked for)

**Analysis type:** (coverage gap assessment | impact analysis before deletion | packaging boundary evaluation | mixed)

## Context Gathered

- **Target deployment channel:** (Metadata API / Unlocked Packages / 2GP Managed / SFDX Source Tracking)
- **API version:** (e.g., v62.0)
- **Org edition:**
- **Components under evaluation:** (list or describe scope)
- **Packaging strategy in place?** (monolithic / multi-package / none)

## Coverage Gap Analysis

| # | Metadata Type | Metadata API | Source Tracking | Unlocked Pkg | 2GP Managed | Workaround |
|---|---|---|---|---|---|---|
| 1 | | Supported / Not / Beta | | | | |
| 2 | | | | | | |

### Unsupported Types Requiring Manual Steps

| Metadata Type | Workaround | Documented In |
|---|---|---|
| | | |

## Dependency Graph Results

### Target Component(s)

| Component Name | Component Type | Analysis Direction |
|---|---|---|
| | | Upstream / Downstream / Both |

### Upstream Dependencies (what this component depends on)

| Referenced Component | Type | Hard/Soft | Notes |
|---|---|---|---|
| | | | |

### Downstream Dependencies (what depends on this component)

| Dependent Component | Type | Hard/Soft | Impact if Removed |
|---|---|---|---|
| | | | |

## Impact Analysis (if deletion/refactoring)

- **Components targeted for change:**
- **Hard dependencies that must be resolved first:**
- **Soft dependencies (informational):**
- **Sandbox testing plan:**

## Packaging Boundary Evaluation (if applicable)

| Candidate Package | Internal Edges | External Edges | Cohesion Rating |
|---|---|---|---|
| | | | High / Medium / Low |

### Cross-Package Dependencies

| Source Package | Target Package | Dependency Type |
|---|---|---|
| | | |

## Checklist

- [ ] Metadata Coverage Report checked at target API version
- [ ] MetadataComponentDependency queried for all components in scope
- [ ] Hard vs soft dependencies classified
- [ ] Unsupported types documented with workarounds in release runbook
- [ ] Packaging boundaries validated as acyclic
- [ ] Impact analysis reviewed before proceeding with deletion/refactoring

## Notes

Record any deviations from the standard pattern and why.
