# Knowledge vs External CMS -- Work Template

Use this template when working on content platform decisions for a Salesforce org.

## Scope

**Skill:** `knowledge-vs-external-cms`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Content consumers:** (agents / customers / partners / public visitors -- list all and their channels)
- **Existing CMS investment:** (platform name, content volume, authoring maturity, localization pipeline)
- **Einstein dependencies:** (article recommendations enabled? case deflection configured? suggested articles on case pages?)
- **Experience Cloud in use:** (yes/no, which sites, self-service portal present?)
- **Localization scope:** (number of languages, translation workflow maturity)
- **Rich-media needs:** (video, interactive components, structured layouts, DAM integration)

## Content Type Mapping

| Content Type | Primary Consumer | Requires Einstein? | Rich Media? | Localized? | Recommended Platform |
|---|---|---|---|---|---|
| (e.g., troubleshooting guides) | Agents | Yes | No | No | Knowledge |
| (e.g., product documentation) | Customers | No | Yes | Yes | External CMS |
| (e.g., FAQ) | Both | Yes (agents) | No | Yes | Knowledge + CMS portal via CMS Connect |

## Architecture Decision

**Chosen pattern:** (Knowledge-only / Hybrid split / CMS as source with Knowledge sync)

**Rationale:** (why this pattern fits the context above)

## Federation Design (if hybrid)

- **CMS Connect:** (yes/no, which site, which content types)
- **Knowledge sync integration:** (middleware, MuleSoft, scheduled Apex -- if CMS content must reach agent console)
- **Shared taxonomy:** (tagging convention or category alignment between systems)

## Search Strategy

- **Agent-side:** (Einstein Search over Knowledge -- any promoted terms or weighting?)
- **Customer-side:** (Experience Cloud search -- how are Knowledge and CMS Connect results combined?)
- **Relevance tuning plan:** (separate tuning workstreams per channel)

## Checklist

Copy from SKILL.md review checklist and tick items as completed.

- [ ] Every content type explicitly assigned to Knowledge, CMS, or both
- [ ] Einstein article recommendation and case deflection mapped to Knowledge
- [ ] CMS Connect validated if external content must appear in Experience Cloud
- [ ] Search strategy covers agent-side and customer-side without fragmented results
- [ ] Localization requirements satisfied by chosen platform
- [ ] Content authoring team confirmed workflow acceptability
- [ ] Taxonomy alignment between systems documented

## Notes

Record any deviations from the standard pattern and why.
