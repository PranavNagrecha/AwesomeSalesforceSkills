# Go-To-Market Plan

A ranked launch sequence. The ordering rule: nothing gets submitted anywhere
until the repository survives a thirty-second skim by a stranger. Every external
claim carries a URL and was re-checked on **2026-08-15**; every in-repo
measurement was taken the same day with the command shown.

The artefact you are launching is **not the skill count**. It is the
before/after in the README — the `System.runAs()`-in-production example from
[`../skills/apex/mixed-dml-and-setup-objects/references/llm-anti-patterns.md`](../skills/apex/mixed-dml-and-setup-objects/references/llm-anti-patterns.md).
That is the thing a Salesforce developer recognises in two seconds and a
non-Salesforce reader can still follow. Lead with it everywhere.

---

## Step 0 — GitHub Hygiene (do this first, it takes an hour)

Measured current state, 2026-08-15:

```bash
gh api repos/PranavNagrecha/AwesomeSalesforceSkills \
  --jq '{desc:.description,stars:.stargazers_count,forks:.forks_count,homepage:.homepage,topics:(.topics|length)}'
# -> {"desc":"Open-source Salesforce knowledge layer for AI coding assistants.
#      982+ source-grounded skills, 75 agents, 38-tool MCP server with live-org
#      metadata. pip install sfskills-mcp.",
#     "stars":13,"forks":3,
#     "homepage":"https://pypi.org/project/sfskills-mcp/","topics":20}

gh api repos/PranavNagrecha/AwesomeSalesforceSkills/releases --jq 'length'  # -> 0
git tag                                                                      # -> mcp-v0.4.0 mcp-v0.4.1 mcp-v0.4.4 mcp-v0.4.6
```

| Signal | Now | Problem |
|---|---|---|
| Description | "982+ source-grounded skills, 75 agents, 38-tool MCP server…" | Stale in both directions: the registry says **1,027** skills and **76** agents. The MCP tool count is the only figure that is right |
| Releases | 0 | Nothing to link, nothing to cite, no "what's new" |
| Tags | 4, all `mcp-v0.4.x` | Only the MCP sub-package has ever been versioned |
| Stars / forks | 13 / 3 | Public since 2026-06-17 |
| Homepage | PyPI project page | Fine — points at something real |
| Topics | 20 already set | Fine as-is |
| Social preview | Not returned by the REST API — check the UI | If unset, every share renders as a generic grey card |

The description is the single highest-leverage string in the project: it renders
in GitHub search, in every share card, and in the registry listings below. Fix
it before anything else — and note that the "38-tool MCP server" half is
currently the *only* accurate number in it, which is exactly the kind of
half-stale string that costs credibility.

1. **Rewrite the description.** Lead with the capability, keep one derived
   number, keep the install line.

   ```bash
   gh repo edit PranavNagrecha/AwesomeSalesforceSkills \
     --description "Makes AI coding assistants write Salesforce like a senior practitioner: 1,027 source-grounded skills, each with the LLM anti-patterns it must refuse, plus a 38-tool MCP server for live-org context." \
     --homepage "https://pypi.org/project/sfskills-mcp/"
   ```

   Re-derive the numbers before pasting — `python3 scripts/check_doc_counts.py`
   currently prints: *"1027 skills, 48 active runtime + 14 build + 14 deprecated
   = 76 agents, 38 MCP tools."* Do not describe the MCP tools as "read-only" in
   the description: 37 of the 38 are, but `emit_envelope` writes a local report
   file. "Live-org context" is accurate and shorter.

2. **Cut a real v1.0.0 release.** The four existing tags are MCP-scoped, so the
   library itself has never been released. Notes should open with the
   before/after, not a changelog.

   ```bash
   git tag -a v1.0.0 -m "SfSkills v1.0.0 — 1,027 skills, 48 run-time agents, 38-tool MCP server"
   git push origin v1.0.0
   gh release create v1.0.0 \
     --title "v1.0.0 — Salesforce knowledge layer for AI coding assistants" \
     --notes-file docs/release-plans/v1.0.0.md
   ```

   Write the notes file first — `docs/release-plans/` exists and holds one prior
   plan (`v0.4.4-post-launch.md`) to copy the shape from.

   This is not cosmetic — **the PyPI install path is broken until a release
   exists.** `sfskills-mcp-init` fetches its data bundle from
   `releases/latest/download/sfskills-data.tar.gz`, which 404s today because
   there are no releases:

   ```bash
   curl -sL -o /dev/null -w "%{http_code}\n" \
     https://github.com/PranavNagrecha/AwesomeSalesforceSkills/releases/latest/download/sfskills-data.tar.gz
   # -> 404
   ```

   Two things to check before cutting the release, both in
   `.github/workflows/publish-mcp.yml`. First, the `build` job copies
   `vector_index/` into the bundle but never runs `scripts/build_index.py`, so
   the tarball would ship the three tracked JSON files and none of the index the
   step name promises ("registry + lexical index"). Second,
   `mcp/sfskills-mcp/pyproject.toml` and `src/sfskills_mcp/__init__.py` both read
   **0.4.7** while PyPI has only **0.4.6** and the newest tag is `mcp-v0.4.6`.
   Either ship 0.4.7 (push `mcp-v0.4.7`, which triggers that workflow) or stop
   quoting 0.4.7 as shipped.

3. **Set the social preview image.** UI-only — the GitHub REST API does not
   return this field. Upload a 1280×640 PNG at
   <https://github.com/PranavNagrecha/AwesomeSalesforceSkills/settings> under
   *Social preview*. Put the before/after code contrast on it, not a logo.

4. **Review the 20 existing topics rather than adding more.** They already
   include `salesforce`, `mcp`, `claude`, `cursor`, `agentforce`. The two worth
   adding are `agent-skills` and `claude-code` — neither is currently set, and
   both match the vocabulary the open spec established
   (<https://agentskills.io/specification>).

5. **Answer "is this for me?" in the issue templates.** The three templates
   under `.github/ISSUE_TEMPLATE` (`bug-report.yml`, `skill-request.yml`,
   `mcp-tool-request.yml`; `config.yml` is the chooser configuration, not a
   template) are the second thing a curious visitor opens. Two lines at the top
   of each — who the project is for and what it is not — cost nothing and
   pre-empt the most common wrong assumption ("isn't this just a prompt?").

---

## Ranked channel sequence

Order matters: registries first (evergreen, low-risk), then communities where a
bad first post is expensive, then the annual events.

### 1. The official MCP registry

<https://registry.modelcontextprotocol.io/>, tooling and docs at
<https://github.com/modelcontextprotocol/registry>.

*Accepts:* metadata for MCP servers whose package is already published. The
registry hosts the listing, not the artefact.

*Status:* not listed.

```bash
curl -s "https://registry.modelcontextprotocol.io/v0/servers?search=sfskills"
# -> {"servers":[],"metadata":{"count":0}}
```

*Requires*, per `docs/reference/server-json/official-registry-requirements.md`
and `docs/modelcontextprotocol-io/package-types.mdx` in that repo:

- The package on a supported registry. **PyPI is supported** (`pypi.org` only)
  and `sfskills-mcp` is already there.
- A `server.json`. There is none in this repo — `find . -name server.json`
  returns nothing. That is the actual blocker.
- A namespace you can prove you own. For a GitHub-hosted project that means
  `io.github.pranavnagrecha/*`, authenticated by logging in as that GitHub
  account or publishing from a GitHub Action in that account's repo.
- **PyPI ownership proof**: the string `mcp-name: io.github.pranavnagrecha/<name>`
  must appear in the package README, which becomes the PyPI description. It is
  not there today (`curl -s https://pypi.org/pypi/sfskills-mcp/json | grep -c mcp-name` → 0),
  so this needs a README edit *and* a re-publish before the registry will accept
  the listing.

*Post:* nothing to write — this is pure metadata. Do it first because it is the
only channel with zero social risk.

### 2. The Agent Skills ecosystem

<https://agentskills.io/>, spec at <https://agentskills.io/specification>.

*Accepts:* skills in the open `SKILL.md` format; the site lists tools and
directories built on the standard.

*Requires:* the packages already conform structurally — the spec's only required
frontmatter fields are `name` and `description`, which every package has. What
is missing is a subset worth listing. Do not attempt to publish 1,027 entries;
choose the ten flagship skills that have golden evals (`evals/golden/`) and
publish those as the shop window, pointing back to the repo for the rest.

*Post:* one flagship skill, framed as "here is what a Salesforce skill with its
sources named looks like".

### 3. The Claude plugin directory

Two mirrors, **one submission route**:

- <https://github.com/anthropics/claude-plugins-official> — Anthropic-maintained
  plus an `/external_plugins` tree for third parties.
- <https://github.com/anthropics/claude-plugins-community> — explicitly a
  "read-only mirror … synced nightly from Anthropic's internal review pipeline".
  Its README states that "pull requests opened directly against this repo are
  closed automatically".

*Accepts:* plugins that pass automated security scanning and quality review.

*Requires:* submission through the form at
<https://clau.de/plugin-directory-submission> (it redirects to the "submit your
plugin" section of <https://code.claude.com/docs/en/plugins>). **Do not plan a
pull request** — that route is closed by policy, and the previous version of
this document had it wrong.

The packaging itself already exists: `.claude-plugin/plugin.json` and
`.claude-plugin/marketplace.json` are on the default branch, and they solve the
sizing problem. A flat 1,027-skill plugin is not viable — the descriptions alone
total 517,654 characters — so the manifest ships 12 router skills under
`.claude/skills/` (a top-level entry point plus one per domain), whose own
descriptions total 7,361 characters. Each domain router points at a
`references/skill-index.md` roster; exactly one roster is ever opened, and the
1,027 packages are reached by path from there.

Be precise about how those routers work when you describe them, because it is
the part reviewers will test. Each router lists **three** lookup mechanisms in
order: (1) the shipped roster, which always works with no setup; (2) the MCP
`search_skill` tool, if the server is connected; (3)
`scripts/search_knowledge.py`, which needs a local `build_index.py` run because
`vector_index/` is gitignored and never ships. An installed plugin with no MCP
server and no index still resolves skills via mechanism 1 — that is the
behaviour to verify end-to-end before submitting.

*Post:* the plugin itself; the directory listing is the post.

### 4. SFXD Discord

<https://discord.com/invite/sfxd>, community index at <https://sfxd.github.io/>.

*Accepts:* practitioner discussion. **19,118 members** on 2026-08-15, read from
the invite API rather than any published figure:

```bash
curl -s 'https://discord.com/api/v9/invites/sfxd?with_counts=true' \
  | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['guild']['name'], d['approximate_member_count'])"
# -> SFXD - Salesforce X Discord 19118
```

*Requires:* read `#basic-info` first — the rules live inside the server and are
not published on the public web. Budget a few weeks of genuinely answering other
people's questions before posting anything of your own, and keep self-promotion
out of the specialist help channels.

*Post:* the anti-pattern example as a discussion starter — "here are the six
things every model gets wrong about mixed DML" — with the repo as a footnote.

### 5. r/salesforce

<https://www.reddit.com/r/salesforce/>.

*Accepts:* tooling posts when they are useful first and promotional second.

*Requires:* the subreddit's own rules, which are the binding constraint and are
readable without an account at
<https://old.reddit.com/r/salesforce/about/rules.json>. Read them the day you
post — moderators change them. Reddit's site-wide policy is at
<https://redditinc.com/policies/content-policy>. Disclose your affiliation.

(An earlier version of this page cited a marketing blog for a "90/10
participation ratio". That is not a rule published by Reddit or by r/salesforce
and has been removed rather than re-sourced.)

*Post:* "I catalogued the Salesforce mistakes LLMs make, per topic" with three
real anti-patterns inline and the link at the bottom. The post should stand
alone if nobody clicks.

### 6. Trailblazer Community

<https://trailhead.salesforce.com/trailblazer-community>, group directory at
<https://trailhead.salesforce.com/trailblazer-community/groups>.

*Accepts:* posts inside topic groups (Developer, DevOps, Architects) rather than
a global feed.

*Requires:* a Trailblazer account and membership in the relevant group;
engagement norms are heavily Salesforce-employee-adjacent, so frame it as
community tooling, never as a product.

*Post:* the MCP server angle — "let your AI check the org before it suggests a
change" — which lands better with admins than the Apex example.

### 7. LinkedIn

<https://www.linkedin.com/>. The Salesforce ecosystem lives there far more than
on X.

*Accepts:* anything, which is why it converts poorly unless it is specific.

*Requires:* nothing but a post. Tag nobody in the first one.

*Post:* a single image of the before/after code with the platform rule spelled
out in the caption. Repeat monthly with a different anti-pattern; 1,027
`llm-anti-patterns.md` files are an effectively unlimited supply.

### 8. Salesforce Ben

<https://www.salesforceben.com/write-for-us/>.

*Accepts:* guest articles from ecosystem practitioners.

*Requires:* an open submissions window. As of 2026-08-15 the page still reads:
"Please note, submissions are closed while we work through our most recent
content pitches. Although we are sorry we can't accept your idea right now, we
plan to open again in the summer, so please check back then." Treat this as
opportunistic — check back rather than plan around it.

*Post:* a long-form piece on AI-generated Salesforce code failure modes, with
the library as the evidence base rather than the subject.

### 9. TDX

<https://www.salesforce.com/tdx/>. The annual developer event is the one
in-person beat worth planning for: a community session or lightning talk reaches
the exact audience, but the call for participation opens months ahead and needs
a track record. Aim at the next cycle, using whatever traction steps 1–8 produce
as the submission's evidence.

---

## Sequencing and what "working" looks like

Steps 0–2 are a single afternoon and unblock everything else. Step 1 needs a
`server.json` and a PyPI re-publish, so it is small but not zero. Step 3 is now
verification-and-submission rather than a build — the manifests exist — but a
directory review has its own latency, so do not let it block steps 4–9.

- **After Step 0:** the repository description, a v1.0.0 release, and a social
  preview all agree with each other and with `scripts/check_doc_counts.py`.
- **After steps 1–2:** SfSkills is discoverable by someone who never visits
  GitHub — searchable in the MCP registry and visible in the skills ecosystem.
- **After steps 4–7:** the measure is issues and questions, not stars. A stranger
  opening an issue about a specific skill is worth more than fifty stars, because
  it proves someone read past the README.
- **Before Step 8 or 9:** you need a story with numbers in it — "N teams
  installed it, here is what it caught" — which none of the earlier steps
  produce on their own. Do not pitch until you have one.

The failure mode to avoid: posting the skill count. It reliably produces "can't
the model already do this?", which is the argument you cannot win in a comment
thread — particularly since this repo has no with-library/without-library
measurement to answer it. Post the wrong code and the right code, side by side,
and let the reader decide whether their assistant would have caught it.

---

## Channels deliberately left off the list

- **Product Hunt / Hacker News.** Both reward novelty over usefulness, and the
  audience overlap with working Salesforce practitioners is small. A "Show HN"
  with 13 stars behind it converts a one-shot spike into nothing.
- **X / Twitter.** Cross-post if it is free; do not invest there.
- **Paid promotion of any kind.** There is no funnel to send traffic into yet.
  Spend the effort on getting the Step 3 plugin listed instead.
- **The AppExchange** (<https://appexchange.salesforce.com/>). This is a
  developer-tooling library, not a packaged Salesforce app; there is nothing to
  list.

---

*Verified 2026-08-15.*
