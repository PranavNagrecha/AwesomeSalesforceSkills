# LLM Anti-Patterns — Lightning Bolt Template Authoring

Mistakes AI assistants commonly make when an admin asks for help with Lightning Bolt distribution. Each pattern is grounded in a real misalignment between common training-set framing and Salesforce-specific Bolt semantics.

---

## Anti-Pattern 1: Conflating Lightning Bolt with managed package

**What the LLM generates:** "To distribute your community to multiple orgs, create a managed package containing the `ExperienceBundle` and Apex classes, then list it on AppExchange."

**Why it's wrong:**

- Managed packages and Lightning Bolts are different shapes for different problems. A Bolt distributes an Experience site as a *template*; a managed package distributes *behavior* (Apex, custom objects, LWC).
- An `ExperienceBundle` *can* technically be included in a managed package, but it ships as locked metadata — subscriber-org admins cannot edit the resulting site, which defeats the purpose of a redistributable site template.
- A Bolt cannot include Apex / custom objects / fields. Lumping them into "create a managed package containing the bundle and Apex" mixes two artifacts that work together as Bolt + companion package, not as one package.

**What to do instead:**

- For *site shape* distribution → use `LightningBolt` metadata (this skill).
- For *behavior* distribution (Apex / objects / fields) → use a managed (2GP) or unlocked package.
- When both are needed, ship them as a co-installed pair, with the package installed first and the Bolt then used to instantiate the site that depends on the package's components.

---

## Anti-Pattern 2: Recommending Lightning Bolt for app distribution that needs CRUD on custom objects

**What the LLM generates:** "Build your CRM application as a Lightning Bolt — that way customers can install the entire app including data model and business logic from AppExchange."

**Why it's wrong:**

- Bolts cannot carry custom objects, fields, Apex, validation rules, or any data-model metadata. There is nothing in the `LightningBolt` metadata reference that supports CRUD-bearing components.
- "App on AppExchange" is the use case for a managed (2GP) package, not a Bolt. The misuse here is confusion between two different AppExchange listing types.

**What to do instead:**

- If the deliverable includes CRUD logic against custom objects, build a managed package. The `LightningBolt` skill is not the right tool.
- A community starter that *uses* an app's data model can be shipped as Bolt + managed package, with the Bolt declaring the package as a prerequisite in its listing.

---

## Anti-Pattern 3: Misunderstanding what gets exported

**What the LLM generates:** "Export the community as a Bolt — this includes all data, files, CMS content, and custom code so customers get a fully working community on install."

**Why it's wrong:**

- A Bolt explicitly excludes data, CMS content, files, and Apex / custom objects / fields. The platform documentation is unambiguous on this point.
- Customers installing the Bolt and instantiating a site will see broken hero banners (no CMS), missing component data (no records), and (if any custom-object pages were referenced) errors at render time.

**What to do instead:**

- Be explicit about what a Bolt contains: `ExperienceBundle`, `Theme` / `BrandingSet`, listed `flowCategories` (and the flows in them), `customApps`, `images`, `industries`. Nothing else.
- When advising on a Bolt build, walk through the dependency map: what data needs to ship separately, what CMS content needs migration, what objects/Apex need a companion package.

---

## Anti-Pattern 4: Treating `versionNumber` like a managed package version

**What the LLM generates:** "Bump `versionNumber` to 2.0 and your existing customer installs will pick up the new version automatically. Mark old versions as deprecated to force upgrade."

**Why it's wrong:**

- `LightningBolt.versionNumber` is a free-form label, not a semantic-versioning upgrade contract. It doesn't establish a relationship between Bolt versions on the platform side.
- Existing instantiated sites are forks. They have no link back to the Bolt. Re-deploying a higher-versioned Bolt to a target org makes the new template available for *future* `New Site` operations, but does not modify any already-created site.
- "Mark old versions as deprecated to force upgrade" — there is no platform mechanism for this on Bolts.

**What to do instead:**

- Communicate clearly: a Bolt is a starter, not an upgradable artifact. Existing sites do not auto-update.
- Use `versionNumber` for human-readable labeling and listing display. Pair Bolt updates with operational communication to downstream admins about manual change application.
- If true upgrade semantics matter for some part of the deliverable, layer that part into a managed package and ship Bolt + package together.

---

## Anti-Pattern 5: Recommending direct deploy when AppExchange is the right answer (or vice versa)

**What the LLM generates:** Either "always go direct deploy, AppExchange is overkill" or "always use AppExchange so customers can self-serve install."

**Why it's wrong:**

- Direct deploy is fine for ≤3 internal target orgs where you have admin access. It scales poorly past that — no audit trail, no install history, no self-service.
- AppExchange listing is the right answer for partner / external distribution but adds latency (listing review process) and ceremony (Partner Business Org setup) that's overkill for internal-only multi-BU reuse.
- The common LLM failure is to default to one or the other based on training data without examining the distribution context.

**What to do instead:**

- Match the distribution channel to the audience: known internal orgs ≤3 → direct deploy; known internal multi-BU 4+ → unmanaged or unlocked package wrapping the Bolt; external partners or customers → AppExchange Bolt listing.
- For Bolts without Apex / custom objects, AppExchange listing skips security review, so the latency objection is overstated for pure-Bolt artifacts. Reconsider AppExchange even for medium-size distributions if the audit-trail and self-serve-install benefits matter.

---

## Anti-Pattern 6: Hardcoding source-org references in Bolt content

**What the LLM generates:** Example navigation menu config:

```xml
<NavigationMenuItem>
    <label>Partner Registration</label>
    <target>https://acme-source.my.site.com/partners/registration</target>
    <type>ExternalLink</type>
</NavigationMenuItem>
```

**Why it's wrong:**

- The hardcoded URL points at the *source* org's Experience site, not the target org's. After Bolt instantiation in a different org, clicking this menu item navigates the user to the source org's site (or fails if the source URL is private).
- Same hazard applies to hardcoded record IDs, hardcoded named credentials referencing source-org-specific endpoints, and hardcoded org IDs in custom HTML blocks.

**What to do instead:**

- Use relative paths (`/partners/registration`) for in-site navigation.
- For external links that vary by tenant, parameterize via custom metadata or custom labels that the target-org admin sets at install time, and document that requirement in the Bolt's installation guide.
- Run the bundled checker (`scripts/check_lightning_bolt_template_authoring.py`), which scans `ExperienceBundle` JSON and `NavigationMenu` XML for `https://` URLs and `00[0-9a-zA-Z]{15,18}` record-ID patterns and flags them for review.

---

## Anti-Pattern 7: Suggesting CMS content "comes along for the ride"

**What the LLM generates:** "Just export the community as a Bolt and your CMS workspace, content nodes, and editorial drafts will all come with it to the target org."

**Why it's wrong:**

- Enhanced CMS lives in `ManagedContentType`, `ManagedContent`, and `ContentVersion` — separate metadata types that are not bundled by `LightningBolt`. The community references them by ID/name, but the actual content nodes do not move.
- After Bolt instantiation, CMS-driven components render as "Content not found" until the target-org admin authors or migrates equivalent content.

**What to do instead:**

- Be explicit: CMS content is NOT in the Bolt. List the CMS workspaces and key content nodes the Bolt references in the installation guide so target-org admins know what they need to author or migrate before / after instantiation.
- For static branding assets that don't need editorial workflow, recommend storing them as `staticresources` instead of CMS content. Static resources DO ship with metadata deploys and survive a Bolt distribution cleanly.
