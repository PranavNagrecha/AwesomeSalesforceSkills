# Well-Architected Notes - List Views And Compact Layouts

## Relevant Pillars

### User Experience

These features directly affect how quickly users recognize records, pick the next item to work, and trust what they are seeing on desktop and mobile.

### Operational Excellence

List-view governance matters operationally. Without ownership and review, every object turns into a cluttered set of duplicate queues that are expensive to support.

### Reliability

Reliable work routing is not only about automation. If the browse surface is noisy or misleading, users process the wrong records or miss urgent ones.

## Architectural Tradeoffs

- **Fewer governed views vs user freedom:** Unlimited shared views feel flexible, but they increase clutter and inconsistency.
- **More highlight fields vs scan speed:** Adding information seems helpful until the highlights panel stops functioning as a fast recognition layer.
- **One generic setup vs persona-specific tuning:** Generic browse surfaces are cheaper to administer, but they often fail the real workflow.

## Anti-Patterns

1. **Public list-view sprawl** - too many near-duplicate views make the object harder to navigate than the records themselves.
2. **Overloaded compact layouts** - treating the highlights panel like a mini page layout destroys scanability.
3. **Trying to solve search and browse with the same configuration** - each surface serves a different user question and needs separate tuning.

## Official Sources Used

- Metadata API Developer Guide (v62 PDF), `ListView`, `ListViewFilter`, `FilterScope` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (the `filterScope` enumeration, the `operation` enumeration, `booleanFilter` positional indexing, the `queue` field and its auto-created list view, the `PC_` person-account column prefix, and the note that "Visible only to me" views aren't accessible in Metadata API)
- Metadata API Developer Guide (v62 PDF), `SharedTo` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (the `group` / `role` / `territory` / `queue` sharing targets, and the statement that `SharedTo` is absent from the metadata of public list views — the basis for the checker's public-view rule)
- Metadata API Developer Guide (v62 PDF), `CompactLayout` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (field order as prioritisation, the four unsupported field types, and `compactLayoutAssignment` on both `CustomObject` and `RecordType`)
- Metadata API Developer Guide (v62 PDF), `SearchLayouts` and `ProfileSearchLayouts` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (`listViewButtons`, `searchResultsAdditionalFields`, `lookupDialogsAdditionalFields`, the Name-field re-add behaviour, and the profile/tab prerequisites for deploying per-profile search results)
- Metadata API Developer Guide (v62 PDF), "Sample package.xml Manifest Files" → List Views for Standard Objects — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (the `objectName.listViewUniqueName` members syntax and the per-type wildcard rules used in references/metadata-examples.md)
- Object Reference for the Salesforce Platform (v62 PDF), `ListView` standard object — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf (`SobjectType`, `DeveloperName`, `Name`, `IsSoqlCompatible`, and the supported calls behind the post-deploy verification query)
- Compact Layouts (Help) - https://help.salesforce.com/s/articleView?id=sf.compact_layout_overview.htm&type=5 (compact layouts as the highlights-panel and mobile-card surface)
- List Views (Help) - https://help.salesforce.com/s/articleView?id=sf.customviews.htm&type=5 (list views as the browse-and-filter surface)
- Manage List View Sharing and Editing with Granular Permissions (Summer '26 Release Notes) - https://help.salesforce.com/s/articleView?id=release-notes.rn_listviews_share_private.htm&language=en_US&release=262&type=5 (the "Manage Shared List Views" permission split covered in SKILL.md gotcha 5)
- Salesforce Well-Architected Overview - https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (the pillar framing above)
