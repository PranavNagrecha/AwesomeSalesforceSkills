# Gotchas — Salesforce CLI Automation

Non-obvious Salesforce platform behaviors that cause real production problems when scripting the CLI.

## Gotcha 1: Mixing `sf` and legacy `sfdx` installs on one runner

**What happens:** Two different global installations can disagree on config paths, plugin sets, and supported flags. Jobs may pass on one agent image and fail on another.

**When it occurs:** Docker images or VM images that still install `sfdx-cli` while also installing `@salesforce/cli`, or golden images updated incrementally without removing the old toolchain.

**How to avoid:** Standardize on a single supported installation path per the Salesforce CLI documentation; pin the CLI version in the image or bootstrap script and remove deprecated packages from install lines.

---

## Gotcha 2: Assuming exit code alone proves success

**What happens:** Commands that enqueue asynchronous work (or return early when `--wait` is missing) can exit zero while the org is still processing or later reports failure.

**When it occurs:** Long deploys, large test suites, or bulk data jobs where the default wait window is shorter than org processing time.

**How to avoid:** Always set an explicit `--wait` with headroom, or implement async polling using the job identifiers returned in `--json` output per the CLI reference for that command family.

---

## Gotcha 3: Progress UI corrupting captured logs

**What happens:** ANSI progress output interleaves with JSON lines when stdout is tee’d to a file, producing invalid JSON for parsers.

**When it occurs:** CI environments without a TTY still sometimes render progress unless disabled consistently.

**How to avoid:** Set `SF_USE_PROGRESS_BAR=false` (or follow your platform’s equivalent convention) and prefer `--json` for anything a script consumes.
