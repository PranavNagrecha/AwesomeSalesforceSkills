# Examples — Release Notes Automation

## Example 1: GitHub Action — Conventional Commits + Salesforce metadata diff

**Context:** Team tags `vYYYY.MM.PATCH` weekly. Commit messages follow Conventional Commits.

**Problem:** Release notes are manually copy-pasted from `git log` and routinely miss commits.

**Solution:**

```yaml
name: release-notes
on:
  push:
    tags: ['v[0-9]*']

jobs:
  notes:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }

      - id: prev
        run: |
          PREV=$(git describe --tags --abbrev=0 --match 'v[0-9]*' "${GITHUB_REF_NAME}^" || true)
          echo "prev=$PREV" >> "$GITHUB_OUTPUT"

      - id: notes
        run: |
          python3 .ci/release_notes.py \
            --from "${{ steps.prev.outputs.prev }}" \
            --to "${GITHUB_REF_NAME}" \
            --salesforce-source force-app \
            --output RELEASE_NOTES.md

      - uses: softprops/action-gh-release@v2
        with:
          body_path: RELEASE_NOTES.md
```

**Why it works:** `fetch-depth: 0` ensures `git describe` can see prior tags. The Python script handles parsing, grouping, and the metadata-diff append.

---

## Example 2: Jira-keyed categorization with caching

**Context:** Commits look like `ABC-1234: Fix discount engine race`. Stakeholders want issue-type-grouped notes.

**Problem:** A naive script calls Jira once per commit; a 200-commit release exhausts the rate limit.

**Solution:**

```python
JIRA_KEY = re.compile(r"\b([A-Z][A-Z0-9]+-\d+)\b")
issue_cache: dict[str, dict] = {}

def fetch_issue(key: str) -> dict:
    if key in issue_cache:
        return issue_cache[key]
    r = session.get(f"{JIRA}/rest/api/3/issue/{key}",
                    headers={"Authorization": f"Bearer {TOKEN}"})
    r.raise_for_status()
    issue_cache[key] = r.json()
    return issue_cache[key]

def categorize(commits):
    buckets = {"Story": [], "Bug": [], "Task": [], "Other": []}
    for c in commits:
        keys = set(JIRA_KEY.findall(c.subject))
        if not keys:
            buckets["Other"].append(c.subject); continue
        for k in keys:
            issue = fetch_issue(k)
            t = issue["fields"]["issuetype"]["name"]
            buckets.setdefault(t, []).append(
                f"- {k}: {issue['fields']['summary']}"
            )
    return buckets
```

**Why it works:** Per-key cache reduces 200 commits with ~80 unique keys to 80 API calls. Tokens come from the pipeline secret manager.

---

## Anti-Pattern: regenerating notes on every push

**What practitioners do:** Wire the workflow to `push: branches: [main]` so notes regenerate every commit.

**What goes wrong:** The "release notes" become a rolling diff with no anchor; stakeholders lose track of what was actually shipped versus what's in flight.

**Correct approach:** Trigger on tag push (or on the deployment-promotion job). Notes anchor to a specific tagged release that exists in the change-management trail.
