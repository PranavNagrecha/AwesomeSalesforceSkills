# LLM Anti-Patterns — Release Notes Automation

Common mistakes AI coding assistants make when generating or advising on release-notes pipelines.

## Anti-Pattern 1: Calling Jira API per commit without caching

**What the LLM generates:**

```python
for commit in commits:
    issue = jira.issue(commit.key)
    notes.append(issue.fields.summary)
```

**Why it happens:** Naive per-iteration API call without the obvious cache.

**Correct pattern:**

```python
cache: dict[str, dict] = {}
for key in unique_keys(commits):
    cache[key] = jira.issue(key)
```

Reduce N commits to U unique tickets (typically a 3–5x reduction) and cache.

**Detection hint:** No `cache`, `dict`, or `lru_cache` adjacent to a Jira/GitHub API call inside a commit loop.

---

## Anti-Pattern 2: Forgetting `fetch-depth: 0`

**What the LLM generates:** A workflow YAML that uses `actions/checkout@v4` with default settings, then runs `git describe`.

**Why it happens:** Default checkout works for most CI tasks; tag-aware tasks are an exception.

**Correct pattern:**

```yaml
- uses: actions/checkout@v4
  with: { fetch-depth: 0 }
```

**Detection hint:** Any `git describe`, `git log <range>`, or `git tag` invocation in CI without an explicit `fetch-depth: 0` in the checkout step above it.

---

## Anti-Pattern 3: Embedding Jira tokens in the workflow file

**What the LLM generates:**

```yaml
env:
  JIRA_TOKEN: "ATATT3xFfGF0..."
```

**Why it happens:** Wants the example to "just work."

**Correct pattern:** Reference a repo or organization secret: `JIRA_TOKEN: ${{ secrets.JIRA_TOKEN }}`. See `devops/pipeline-secrets-management`.

**Detection hint:** Any literal string of >20 alphanumeric chars assigned to a token-shaped env var.

---

## Anti-Pattern 4: Generic categorization that ignores the team's convention

**What the LLM generates:** Hard-coded buckets `Features / Fixes / Other` regardless of what the team uses.

**Why it happens:** Default to Keep a Changelog without checking what the repo actually does.

**Correct pattern:** Inspect existing notes, sample commit messages, and ticket types. Mirror the team's own taxonomy or propose one explicitly before coding.

**Detection hint:** A categorizer that doesn't reference any team-specific constant or config file.

---

## Anti-Pattern 5: Replacing instead of appending the metadata-diff section

**What the LLM generates:** A pipeline that overwrites RELEASE_NOTES.md with only the metadata diff, losing the human-readable Jira section.

**Why it happens:** The two generators were written separately; the second clobbers the first.

**Correct pattern:** Compose sections in a single render step. Either generate one Markdown document end-to-end, or use a templating step that explicitly appends.

**Detection hint:** Two separate `> RELEASE_NOTES.md` redirects in the same job.
