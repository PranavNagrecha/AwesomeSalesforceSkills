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

- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
  Used to confirm `CustomApplication` and `CustomTab` are standard Salesforce metadata types.
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
  Used to confirm `CustomApplication` metadata structure, `navItems` subelement, and `CustomTab` types.
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
  Used to frame Security and Operational Excellence pillar guidance for app and tab configuration best practices.
- Salesforce Help — Create and Edit Lightning Experience Apps: https://help.salesforce.com/s/articleView?id=sf.app_builder_apps.htm
  Primary reference for App Manager workflow, navigation items, utility bar, and profile visibility configuration.
- Salesforce Help — Custom Tabs: https://help.salesforce.com/s/articleView?id=sf.custom_tabs.htm
  Primary reference for tab types, tab creation steps, and profile tab settings behavior.
