# Well-Architected Notes — App and Tab Configuration

## Relevant Pillars

- **Security** — App visibility by profile or permission set is the first layer of access control for Salesforce features. A well-configured app exposes only the objects, tabs, and utilities relevant to the user's role, reducing attack surface and accidental data exposure. Profile tab settings add a second layer: tabs can be hidden entirely from profiles that should never access an object.
- **Operational Excellence** — Purpose-built apps improve user adoption and reduce training burden. When each team has an app tailored to their workflow, onboarding is faster, navigation errors decrease, and support requests drop. Naming conventions for app API names (snake_case, role-based prefixes) make deployments repeatable and CI/CD pipelines reliable.
- **Reliability** — App configuration is metadata — it is deployable via Metadata API and SFDX. Keeping app definitions in source control prevents configuration drift between sandboxes and production.

## Architectural Tradeoffs

**Standard navigation app vs console app:** Console apps provide split-view and a persistent work queue, which increases throughput for agents handling many records simultaneously. However, console apps require additional licenses for most users and have a steeper learning curve. Use console apps only when the team's workflow is genuinely queue-driven; standard navigation apps are sufficient for most internal users.

**Profile-based visibility vs permission-set-based visibility:** Historically, app visibility was only controllable at the profile level, driving profile proliferation. As of recent releases, permission-set-based app visibility allows admins to control which users see an app without creating separate profiles. This is the preferred approach when different subsets of the same profile need different app visibility, because it avoids the long-term maintenance burden of many near-identical profiles.

**Utility bar scope:** Utility bar components run for every user who has the app open, regardless of whether they use the utility. Custom LWC utilities that make callouts or run heavy logic on load increase page load time for all users of the app. Keep utility components lightweight and lazy-loading where possible.

## Anti-Patterns

1. **Creating one app for all users** — A single "catch-all" app assigned to all profiles exposes irrelevant objects to every user, increases navigation noise, and makes it harder to tailor the experience for each team. Build purpose-built apps per team or role and assign them to the relevant profiles.
2. **Relying on app visibility alone for security** — App visibility controls what appears in the UI, but it does not prevent API access to objects or fields. A user who cannot see the Accounts tab in their app can still query Account records via the API. Real data security requires proper profile object permissions and field-level security, independent of app visibility.
3. **Configuring utility bar without mobile testing** — Adding a utility bar and assuming it works everywhere leads to broken mobile experiences. Always test the app on the Salesforce mobile app if mobile users are in scope, and document explicitly which features are desktop-only.

## Official Sources Used

- **Metadata API Developer Guide — `CustomApplication`** (v62 PDF, `api_meta.txt` L39621–40737) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
  Source for the `tabs` element and the `standard-` prefix rule (L39767–39775), `defaultLandingTab` (L39661–39663), `navType` / `uiType` both being "Not updateable" (L39719, L39782), `formFactors` semantics (L39666–39685), `AppBrand` (L39873–39893), `utilityBar` sharing across apps (L39788–39795), `AppWorkspaceConfig` / `WorkspaceMapping.fieldName` (L40028–40047), the destructive-change restriction on `profileActionOverrides` (L40398–40407), wildcard support (L40734–40736), and both sample app definitions (L40450–40525, L40527–40725).
- **Metadata API Developer Guide — `CustomTab`** (v62 PDF, `api_meta.txt` L47248–47467) — same PDF
  Source for the "only one of `auraComponent` / `customObject` / `flexiPage` / `lwcComponent` / `page` / `scontrol` / `url`" rule (L47276–47285), `motif` being required and its value catalogue (L47362–47396), `frameHeight` being required for s-control and page tabs (L47319–47320), `label` documented for web tabs (L47341), and `urlEncodingKey` (L47437–47441).
- **Metadata API Developer Guide — `FlexiPage`** (v62 PDF, `api_meta.txt` L66865–68023) — same PDF
  Source for `type` `UtilityBar` being a Lightning page used as the utility bar, API 38.0+ (L67084–67086); for the utility bar being the only page type that supports component decorators, which is where a utility's width, height, and label live (L67353–67366); and for the `Background` region type supported for utility bars only (L67288–67292).
- **Metadata API Developer Guide — `PermissionSet` and `Profile`** (v62 PDF, `api_meta.txt` L94903–94910, L95142–95161, L97897–97907, L98243–98266) — same PDF
  Source for `PermissionSetApplicationVisibility` (`application` + `visible`), `PermissionSetTabSetting` (`Visible` / `Available` / `None`), `ProfileApplicationVisibility` (with its required `default` flag, one app per profile), and `ProfileTabVisibility` (`DefaultOn` / `DefaultOff` / `Hidden`) — the four shapes that decide whether anyone can open the app.
- **Object Reference for Salesforce — `AppDefinition`, `TabDefinition`, `AppTabMember`, `AppMenuItem`** (v62 PDF, `object_reference.txt` L34140–34330, L277676–277775, L36689–36760, L34561–34900) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
  Source for the post-deploy verification queries: `AppDefinition` returns "Metadata … only for apps that the current user can access", `TabDefinition` "Returns only the tabs that the current user has access to", `AppTabMember.SortOrder` / `WorkspaceDriverField` expose the app's own tab order and console mapping, and `AppMenuItem.IsVisible` is the org-wide App Launcher toggle (the only updateable field on that object).
- **Salesforce Developer Limits and Allocations Quick Reference** (`salesforce_app_limits_cheatsheet.txt`, last updated 7 August 2026) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf
  Used as a *negative* result: it states that it does not cover "User interface elements in the Salesforce application" and refers per-edition allocations to *Salesforce Features and Edition Allocations* (cheat sheet L11–17). That is the grounding for the UNVERIFIED marker on the 50-navigation-item claim in `SKILL.md`.
- **Salesforce Well-Architected** — https://architect.salesforce.com/well-architected/overview
  Used to frame the Security and Operational Excellence pillar sections above; the platform behaviour claims in this skill are grounded in the two PDFs, not here.
