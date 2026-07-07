# Live Preview Session Runbook — LWC Local Development

A copy-paste runbook for an `sf lightning dev` preview session. Fill the placeholders,
pick the command for your surface, and keep the reload cheat sheet in view.

## Session context

- **Target org (sandbox/scratch only):** `_______________`  (alias for `--target-org`)
- **Surface:** [ ] single component  [ ] Lightning app  [ ] Experience (LWR) site
- **Component / app / site name:** `_______________`
- **Mobile?** [ ] no  [ ] iOS (Xcode installed)  [ ] Android (Android Studio installed)

## 0. One-time setup

```bash
# Install / update the Live Preview plugin
sf plugins install @salesforce/plugin-lightning-dev

# Confirm you have a project and an authenticated org
sf project deploy start --dry-run -o <org>   # sanity check the project + auth
python3 check_lwc_local_development.py --project-dir .   # readiness check
```

Enabling on first run requires the **View Setup** and **Customize Application** permissions;
the CLI prompts to enable the feature — press Enter or type `y`.

## 1. Start the preview (pick ONE)

```bash
# Single component in isolation (fastest inner loop; gets LDS/Apex data)
sf lightning dev component -o <org> -n <componentName>
# ...or choose the component in the browser:
sf lightning dev component -o <org> -c

# Full Lightning app (app-level navigation + cross-component context)
sf lightning dev app -o <org> -n <AppName>
sf lightning dev app -o <org> -n <AppName> --device-type ios       # requires Xcode
sf lightning dev app -o <org> -n <AppName> --device-type android   # requires Android Studio

# Experience (LWR) site — desktop only
sf lightning dev site -o <org> -n <SiteName>
```

## 2. Edit + reload cheat sheet

| Edit | Reloads how |
|---|---|
| HTML / template attributes | Auto on save |
| Basic CSS | Auto on save |
| Reference to a new component | Auto on save |
| JS method change (no public-API change) | Auto on save |
| New / deleted file | Auto on save |
| **New `@api` property or method** | **Manual** |
| **`@wire` change (config, import, decorator, GraphQL)** | **Manual** |
| **New `@salesforce` scoped-module import** | **Manual** |
| **`.js-meta.xml` update** | **Manual** |

**Manual reload:**
- Single component → refresh the browser page.
- App / site → `sf project deploy start` the changed metadata, then restart the dev server.

## 3. Guardrails

- [ ] Org is a **sandbox or scratch** org, not production.
- [ ] Not trying to preview an **Aura** component (LWC-only).
- [ ] Mobile SDK (Xcode / Android Studio) installed if using `--device-type`.
- [ ] Maturity noted where relevant: single-component preview was Beta in Winter '26, GA
      ("Single Component Live Preview") the week of April 13, 2026; VS Code React preview is Beta.

## 4. Exit the inner loop

- [ ] Ran Jest (`lwc/lwc-testing`) — preview renders, it doesn't assert.
- [ ] Deployed through the normal pipeline — preview is not a release step.

## Notes

_Record any manual-reload surprises or environment quirks here._
