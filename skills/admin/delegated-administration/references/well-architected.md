# Well-Architected Notes — Delegated Administration

## Relevant Pillars

- **Security** — Delegated administration is a direct implementation of the principle of least privilege. Rather than granting System Administrator access for routine user management tasks, it scopes admin rights to only the users, profiles, and objects that a business role legitimately needs to manage. Poorly configured groups (overly broad role scope, unrestricted assignable profiles) create privilege escalation vectors. The platform enforces one hard security boundary: System Administrator users are always protected from delegated admin actions.

- **Operational Excellence** — Delegated administration reduces the operational bottleneck of centralizing all user management with the Salesforce admin team. By delegating routine tasks (onboarding, password resets, profile assignments) to regional or departmental coordinators, the admin team can focus on architecture-level work. The tradeoff is that the admin team must maintain the Delegated Administrator groups as the org evolves — stale groups, outdated role assignments, and missing profile entries are the primary operational failure modes.

- **Reliability** — Not directly applicable. Delegated administration does not affect org availability or data reliability.

- **Performance** — Not applicable. Delegated administration is a configuration feature with no meaningful performance implications.

- **Scalability** — As the org grows, the number of delegated groups may need to grow proportionally with business units or regions. The feature supports multiple independent groups, which scales well. However, the admin overhead of maintaining group configurations at scale is a real concern — automated auditing (e.g., using the checker script in this skill) is recommended for orgs with many groups.

---

## Architectural Tradeoffs

**Least privilege vs. operational friction:** Tight scoping (narrow role lists, minimal assignable profiles) maximizes security but increases the likelihood that delegated admins encounter "permission denied" scenarios for legitimate tasks. The right balance is to start narrow and expand based on documented operational need, not to start broad for convenience.

**Single large group vs. multiple targeted groups:** A single Delegated Administrator group covering all business units simplifies setup but creates a risk surface — a misconfigured group affects all delegated admins in it. Multiple smaller groups (one per region or department) are safer and easier to audit but require more ongoing maintenance. For orgs with 5+ business units, multiple groups is the recommended architecture.

**Custom object admin rights:** Granting custom object administration reduces change management overhead for fast-evolving custom objects but creates a risk of unauthorized field or validation rule changes that affect downstream integrations or reports. Gate this based on the business unit's maturity and the sensitivity of the object.

---

## Anti-Patterns

1. **Granting full System Administrator profile for convenience** — When a delegated admin frequently hits permission gaps (e.g., can't manage a roleless user, can't touch a System Admin), the path of least resistance is to promote them to full System Administrator. This eliminates the security scoping entirely and is the most common anti-pattern. The correct response is to fix the root cause (assign roles to users, route System Admin requests properly) rather than expanding access.

2. **Configuring assignable profiles that are too permissive** — Including high-privilege profiles (System Administrator, "Power User" with API access) in a Delegated Administrator group's Assignable Profiles list allows the delegated admin to effectively escalate any user's privileges. Assignable profiles should be limited to the specific non-privileged profiles the delegated admin's business role legitimately needs to assign.

3. **Neglecting group maintenance as the org evolves** — Role hierarchies change, profiles are renamed or retired, and business units restructure. Delegated Administrator groups that are not updated become either too broad (old roles that now cover new unintended departments) or broken (assignable profiles that no longer exist). Scheduled audits using the `check_delegated_administration.py` script are the recommended mitigation.

---

## Official Sources Used

- Salesforce Help: Set Up Delegated Administration — https://help.salesforce.com/s/articleView?id=sf.admin_delegate.htm
- Salesforce Help: Delegated Administration Overview — https://help.salesforce.com/s/articleView?id=sf.delegated_admin_overview.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
