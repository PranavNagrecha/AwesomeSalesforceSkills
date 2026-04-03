# Well-Architected Mapping: Permission Sets vs Profiles

---

## Pillars Addressed

### Security

**Principle: Least Privilege**
Every user should have exactly the access they need for their role — no more. The Permission Set model enables this more precisely than Profiles because access is additive and individually assignable.

- WAF check: Are users granted only the objects and fields required for their job function?
- WAF check: Is there an audit trail for permission changes? (PSG assignment logs are queryable)
- WAF check: Are temporary elevated permissions tracked and time-bound?

**How this skill addresses it:**
- The Decision Matrix prevents over-assignment by clarifying when NOT to use Profiles for feature access
- The Minimum Access base profile pattern eliminates profile-as-feature-grant
- Naming conventions make permission scope visible at a glance

**Risk of not following this:** Users retain access from old roles (role creep). Security audits fail. Data exposure through fields users shouldn't see.

### Operational Excellence

**Principle: Maintainability at Scale**
A permission model that requires creating a new Profile every time a new team is onboarded is not maintainable. PSGs enable role changes with a single assignment operation.

- WAF check: Can access be changed without a profile reassignment (which affects all other users on that profile)?
- WAF check: Is there a documented permission model that a new Admin can understand?
- WAF check: Are permission assignments auditable via SOQL?

**How this skill addresses it:**
- Mode 2 (Audit and Migrate) provides a systematic approach to reducing profile count
- SOQL examples make the current state queryable and auditable
- Naming conventions make the permission model self-documenting

**Risk of not following this:** Profile sprawl (50+ profiles in orgs older than 5 years). Access changes require testing entire profiles. No clear audit trail.

---

## Pillars Not Addressed

- **Performance** — Permission model design doesn't directly affect query/page performance.
- **Scalability** — Relevant only in the sense that profile sprawl becomes unmanageable at scale; the PSG model scales better administratively.
- **Reliability** — Not directly relevant to permission model design.
- **User Experience** — Indirectly relevant (users seeing too many or too few fields affects UX), but this skill doesn't address UX design.

---

## Salesforce Well-Architected Reference

**Security pillar:** [architect.salesforce.com/well-architected/security](https://architect.salesforce.com/well-architected/security)

Key principle applied: *"Grant the least amount of access necessary to accomplish the task."*

**Relevant Salesforce guidance:**
- Salesforce Help: User Permissions and Access
- Trailhead: Manage User Profiles and Permission Sets
- Salesforce Architects: Profile Retirement FAQ (check current Salesforce release notes)

## Official Sources Used

- Salesforce Well-Architected Overview — least-privilege and governance framing
- Metadata API Developer Guide — profile and permission metadata movement constraints
