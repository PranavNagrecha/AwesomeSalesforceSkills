# Well-Architected Notes — Record Access Troubleshooting

## Relevant Pillars

Diagnosing record access sits at the intersection of two pillars
that most practitioners think about and three that they often
neglect. Security is dominant — the work is fundamentally about
verifying who can see what — but the way you *do* the diagnosis
determines whether the org's access model becomes more knowable or
more opaque over time.

- **Security (Trusted)** — Dominant pillar. Every grant has a
  `RowCause` and a configurable source; the diagnostic skill exists
  to make that chain auditable. Sloppy diagnosis (granting `View All`
  to make a ticket go away) actively weakens the security model by
  introducing grants whose justification is "to close the ticket."
  Tight diagnosis (rooted in `UserRecordAccess` + `__Share`
  enumeration) leaves an evidence trail that supports SOX, HIPAA,
  and SOC 2 walkthroughs without rework.
- **Operational Excellence (Resilient + Operational)** — Equal to
  Security in importance for this skill. The org is a living system;
  sharing configuration drifts as people add manual shares, build
  one-off sharing rules, and forget the Apex Sharing Reasons their
  predecessors created. A *diagnostic playbook* (this skill) is the
  thing that keeps the system debuggable as it grows. The
  alternative — discovering the access model from scratch on every
  ticket — does not scale past ~500 users.
- **Adaptable (Composable)** — Sharing configuration is the most
  cross-team metadata in the org. Sales, Service, Field Service,
  Finance, and Marketing all configure shares for their objects;
  the platform composes them, and the result is rarely what any one
  team designed. The diagnostic skill is the protocol that lets a
  cross-functional access conversation be grounded in data instead
  of opinion.
- **Performance** — `UserRecordAccess` queries are bounded and fast
  (single user/record pair). `__Share`-table queries on
  high-cardinality objects can be slow (large orgs have millions of
  share rows per object) — index the `ParentId` and `UserOrGroupId`
  predicates and avoid `LIKE` searches. For diagnostic work this is
  rarely the bottleneck; for *programmatic* sharing audits across
  hundreds of records, batch the queries.
- **Reliability** — Sharing recalculation is async and can take
  hours on large orgs. Diagnoses captured during an in-progress
  recalculation can show transient states that don't reflect the
  steady-state access model. Time your diagnostic queries relative
  to known recalculation windows.

## Architectural Tradeoffs

When the diagnosis says "the user genuinely lacks access and should
have it," you have to pick the remediation mechanism. This is the
core tradeoff matrix:

| Remediation | Granularity | Survives owner change? | Visible to admin (UI) | Recalculation cost | When to pick it |
|---|---|---|---|---|---|
| **Change record Owner** | One record | N/A (you ARE the change) | Yes (Owner field) | Per-record share refresh | Owner is genuinely wrong; the new owner should have all the same downstream access the previous owner had |
| **Add Manual Share** | One record, one user/group | NO — wiped on transfer | Yes (Sharing detail) | None | Truly one-off grant; user accepts re-granting after any transfer |
| **Add to Account/Opp/Case Team** | One record, one user, role-typed | YES (team membership persists) | Yes (Team related list) | None | Repeated cross-user collaboration on the same record; the role-name is documentable (Account Manager, Executive Sponsor, etc.) |
| **Add Sharing Rule (owner-based)** | All records owned by group X → group Y | YES (rule re-evaluates on transfer) | Yes (Sharing Settings) | Async recalc (minutes to hours) | A *class* of records should always be visible to a *class* of users; ownership is the right pivot |
| **Add Sharing Rule (criteria-based)** | Records matching field criteria → group Y | YES (re-evaluates when criteria change) | Yes (Sharing Settings) | Async recalc + per-update re-eval | A *class* of records defined by record content (Region, Industry, etc.) should be visible to a group; transcends ownership |
| **Add Apex Managed Share** | Whatever Apex code dictates | YES (RowCause survives transfer) | Yes (Sharing detail shows the RowCause) | Per-insert; you control the recalc trigger | Complex grant logic that can't be expressed as criteria; the share survives owner change AND has an audit-able `RowCause` |
| **Add user to higher Role** | All records owned by their subordinates | YES (role hierarchy is permanent until changed) | Yes (User detail → Role) | Async recalc on role move | Org-design alignment issue, not a sharing issue |
| **Loosen OWD** | All records of the object, everyone | YES (tenant-wide setting) | Yes (Sharing Settings) | Tenant-wide async recalc (can be hours) | The object's privacy model was wrong; resharing one-by-one is infeasible at scale |

This matrix assumes the object has an `Owner` field. A custom object on the
*detail* side of a master-detail relationship does not: per the Object
Reference, *"Custom objects on the detail side of a master-detail relationship
can't have sharing rules, manual sharing, or queues, because these elements
require the Owner field."* None of these rows can be applied to the detail
record itself — apply them to the master, whose access the detail inherits.

The defining axis is **scope vs. precision**. Manual shares and team
membership are surgical but don't compose well. Sharing rules and
role-hierarchy changes are broad but can grant more than intended.
Apex managed sharing is the *one* mechanism that gives you full
control of both axes (custom logic, surviving transfer) at the cost
of building and maintaining the code.

The second axis is **diagnosis cost later**. Manual shares are easy
to grant and hard to audit (you have to enumerate the
`AccountShare WHERE RowCause = 'Manual'` rows and re-establish why
each one exists). Apex managed shares with descriptive `RowCause`
names (`Project_Manager_Access__c`, not `Custom_Share_1__c`) carry
their own justification — the next person debugging the access can
read the `RowCause` and know exactly which Apex grant created it.

A third tradeoff: **fix the user's permissions vs. fix the
configuration**. If two users are both missing access they should
have, the configuration is wrong (a sharing rule isn't matching,
a permset isn't assigned to the right group). If one user is missing
access and 50 others have it correctly, the user's configuration is
wrong (missing role, wrong public group membership, missing permset).
The diagnostic discipline is to ask "how many users have this
problem?" *before* picking the remediation — fixing the wrong tier
creates either over-grants (fixing user-level when config was the
issue) or under-grants (fixing config-level when user-level was the
issue).

## Anti-Patterns

1. **Grant `Modify All Data` to fix a ticket.** Single most damaging
   anti-pattern in the access-troubleshooting domain. Bypasses every
   sharing rule, every Restriction Rule, every FLS check, and every
   Apex `with sharing` guard. Always identifiable in Security Health
   Check as a critical finding. See `examples.md` anti-pattern for
   the full explanation and the remediation hierarchy.
2. **Diagnose visually from the "Sharing" button without running
   `UserRecordAccess`.** The button shows the *winning* grant per
   user; it doesn't enumerate every grant, doesn't surface
   admin-bypass permissions, and doesn't reveal Restriction Rule
   subtraction. Visual diagnosis is wrong about 30% of the time on
   non-trivial sharing models and you won't know which 30%.
3. **Create one-off Manual Shares as the standard remediation.** Manual
   shares are wiped on owner change. A grant that vanishes
   silently when a sales rep leaves the company is a grant that
   produces a re-occurring ticket forever. Use teams or Apex managed
   sharing for grants that should outlive ownership.
4. **Add a sharing rule and test immediately.** Sharing rules
   recalculate async on save — sometimes in seconds, sometimes in
   hours on a large org. Testing the rule against
   `UserRecordAccess` before recalc completes returns a false
   negative; the rule gets re-saved, re-recalc'd, and the org
   accumulates duplicate sharing rules created out of impatience.
   Wait for the "recalculation complete" email or monitor Background
   Jobs before testing.
5. **Delete Apex Sharing Reasons without checking for live share
   rows.** Cascades to all existing shares using that `RowCause` —
   thousands of access grants vanish at once with no warning.
   Always query `<Object>__Share WHERE RowCause = '<name>__c'`
   before deletion; backfill via a new RowCause first if the count
   is non-zero. See `gotchas.md` Gotcha 4.

## Official Sources Used

The following Salesforce documentation pages were treated as the
canonical authority for the behaviors described in this skill. URLs
are reproduced as-cited; substitute the current per-release URL if
the doc layout changes.

- UserRecordAccess SObject Reference —
  https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_userrecordaccess.htm
- Sharing Considerations (Help) —
  https://help.salesforce.com/s/articleView?id=sf.security_sharing_considerations.htm
- Sharing Considerations (Security Implementation Guide) —
  https://developer.salesforce.com/docs/atlas.en-us.securityImplGuide.meta/securityImplGuide/sharing_considerations.htm
- Restriction Rules Developer Guide — Considerations (System Mode
  exemption, View All / Modify All overrides, per-edition rule caps) —
  https://developer.salesforce.com/docs/atlas.en-us.restriction_rules.meta/restriction_rules/restriction_rules_considerations.htm
- View Record Sharing (Help) —
  https://help.salesforce.com/s/articleView?id=sf.users_view_record_sharing.htm
- Organization-Wide Defaults (Help) —
  https://help.salesforce.com/s/articleView?id=sf.security_sharing_owd.htm
- Apex Developer Guide — Understanding Apex Managed Sharing —
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_bulk_sharing_understanding.htm
- Restriction Rules (Help) —
  https://help.salesforce.com/s/articleView?id=sf.security_restriction_rule.htm
- Salesforce Well-Architected — Trusted (Secure) —
  https://architect.salesforce.com/well-architected/trusted/secure
- Apex Developer Guide — Understanding Apex Managed Sharing ("Apex sharing reasons and Apex managed sharing recalculation are only available for custom objects") — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_bulk_sharing_understanding.htm
- Apex Developer Guide — Creating Apex Managed Sharing (share object naming: AccountShare for standard, MyObject__Share for custom) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_bulk_sharing_creating_with_apex.htm
- Object Reference — AccountShare (AccountId, AccountAccessLevel, UserOrGroupId, RowCause) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_accountshare.htm
- Object Reference — Relationships Among Objects (detail object has no Owner field; no sharing rules, manual sharing or queues on the detail side) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/relationships_among_objects.htm
