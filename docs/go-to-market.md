# Go-To-Market Plan

A ranked launch sequence. The ordering rule: nothing gets submitted anywhere
until the repository survives a thirty-second skim by a stranger. Every
external claim carries a URL; every measurement was taken on **2026-07-31**.

The artefact you are launching is **not the skill count**. It is the
before/after in the README — the `System.runAs()`-in-production example from
[`../skills/apex/mixed-dml-and-setup-objects/references/llm-anti-patterns.md`](../skills/apex/mixed-dml-and-setup-objects/references/llm-anti-patterns.md).
That is the thing a Salesforce developer recognises in two seconds and a
non-Salesforce reader can still follow. Lead with it everywhere.

---

## Step 0 — GitHub Hygiene (do this first, it takes an hour)

Measured current state, 2026-07-31
(`gh api repos/PranavNagrecha/AwesomeSalesforceSkills`):

| Signal | Now | Problem |
|---|---|---|
| Description | literally `982+ skills` | Stale and inflated; the registry says 1,027 |
| Releases | 0 GitHub releases | Nothing to link, nothing to cite, no "what's new" |
| Tags | 4, all `mcp-v0.4.x` | Only the MCP sub-package has ever been versioned |
| Stars / forks | 9 / 2 | Public since 2026-06-17 |
| Topics | 20 already set | Fine as-is; no action needed |
| Social preview | not exposed by the REST API — check the UI | If unset, every share renders as a generic grey card |

The description is the single highest-leverage string in the project: it is
what renders in GitHub search, in every share card, and in the registry
listings below. Fix it before anything else.

1. **Rewrite the description and confirm the homepage.** Lead with the
   capability, keep one derived number, keep the install line.

   ```bash
   gh repo edit PranavNagrecha/AwesomeSalesforceSkills \
     --description "Makes AI coding assistants write Salesforce like a senior practitioner: 1,027 source-grounded skills, each with the LLM anti-patterns it must refuse, plus a 38-tool read-only MCP server for live-org context." \
     --homepage "https://pypi.org/project/sfskills-mcp/"
   ```

   Re-derive the numbers before pasting: `python3 scripts/check_doc_counts.py`.

2. **Cut a real v1.0.0 release.** The four existing tags are MCP-scoped, so
   the library itself has never been released. Notes should open with the
   before/after, not a changelog.

   ```bash
   git tag -a v1.0.0 -m "SfSkills v1.0.0 — 1,027 skills, 48 run-time agents, 38-tool MCP server"
   git push origin v1.0.0
   gh release create v1.0.0 \
     --title "v1.0.0 — Salesforce knowledge layer for AI coding assistants" \
     --notes-file docs/release-plans/v1.0.0.md
   ```

   Write the notes file first — `docs/release-plans/` already exists and holds
   one prior plan (`docs/release-plans/v0.4.4-post-launch.md`) to copy the
   shape from.

3. **Set the social preview image.** This is UI-only — the GitHub REST API
   does not expose it. Upload a 1280×640 PNG at
   <https://github.com/PranavNagrecha/AwesomeSalesforceSkills/settings> under
   *Social preview*. Put the before/after code contrast on it, not a logo.

4. **Review the 20 existing topics rather than adding more.** They already
   include `salesforce`, `mcp`, `claude`, `cursor`, `agentforce`. The two
   worth considering are `agent-skills` and `claude-code`, which match the
   vocabulary the open spec established (<https://agentskills.io/specification>).

5. **Answer "is this for me?" in the issue templates.** The three templates
   under `.github/ISSUE_TEMPLATE` (`bug-report.yml`, `skill-request.yml`,
   `mcp-tool-request.yml` — `config.yml` is the chooser configuration, not a
   template) are the second thing a curious visitor
   opens. Two lines at the top of each — who the project is for and what it
   is not — costs nothing and pre-empts the most common wrong assumption
   ("isn't this just a prompt?").

---

## Ranked channel sequence

Order matters: registries first (they are evergreen and low-risk), then
communities where a bad first post is expensive, then the annual events.

1. **The official MCP registry** —
   <https://registry.modelcontextprotocol.io/>, tooling and docs at
   <https://github.com/modelcontextprotocol/registry>.
   *Accepts:* metadata for MCP servers whose package is already published. The
   registry hosts the listing, not the artefact.
   *Requires:* `sfskills-mcp` on PyPI (done —
   <https://pypi.org/project/sfskills-mcp/>, currently 0.4.6), a
   `server.json`, and a reverse-DNS namespace you can prove you own. For a
   GitHub-hosted project that means the `io.github.pranavnagrecha/*` namespace,
   authenticated by logging in as that GitHub account or publishing from a
   GitHub Action in that account's repo.
   *Post:* nothing to write — this is pure metadata. Do it first because it is
   the only channel with zero social risk.

2. **The Agent Skills ecosystem** — <https://agentskills.io/>, spec at
   <https://agentskills.io/specification>.
   *Accepts:* skills in the open `SKILL.md` format; the showcase lists tools
   and directories built on the standard.
   *Requires:* the packages already conform structurally. What is missing is a
   subset worth listing — do not attempt to publish 1,027 entries. Choose the
   ten flagship skills that have golden evals (`evals/golden/`) and publish
   those as the shop window, pointing back to the repo for the rest.
   *Post:* one flagship skill, framed as "here is what a source-graded
   Salesforce skill looks like".

3. **Anthropic's plugin directory** —
   <https://github.com/anthropics/claude-plugins-official>, community mirror
   and submission route at
   <https://github.com/anthropics/claude-plugins-community>.
   *Accepts:* Claude Code plugins meeting quality and security review.
   *Requires:* the packaging now exists — `.claude-plugin/plugin.json` and
   `.claude-plugin/marketplace.json` are in the tree
   (<https://code.claude.com/docs/en/plugin-marketplaces>), and they already
   solve the sizing problem: a flat 1,027-skill plugin is not viable at
   ~127,000 tokens of descriptions, so the manifest ships 12 router skills
   under `.claude/skills/` — one per domain plus a top-level entry point —
   that delegate to `scripts/search_knowledge.py` and the MCP server, with the
   1,027 packages and the run-time agents reached on demand. The
   remaining work is submission, not construction: install the marketplace
   locally, confirm the routers resolve end to end, then open the PR. Note
   that a plugin install still has to reach the retrieval index somehow — the
   routers are only as good as the search behind them, so verify that path
   before submitting.
   *Post:* the plugin itself; the directory listing is the post.

4. **SFXD Discord** — <https://discord.com/invite/sfxd>, community index at
   <https://sfxd.github.io/>.
   *Accepts:* practitioner discussion; 19,115 members on 2026-07-31, read
   from the invite API rather than any published figure:

   ```bash
   curl -s 'https://discord.com/api/v9/invites/sfxd?with_counts=true' \
     | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['guild']['name'], d['approximate_member_count'])"
   # -> SFXD - Salesforce X Discord 19115
   ```

   *Requires:* read `#basic-info` first — the rules live inside the server and
   are not published on the public web (the public listing at
   <https://discord.do/sfxd-salesforce-x-discord/> says only "Please read
   #basic-info before engaging in activity"). The community norm reported by
   members is that self-promotion is tolerated from people who have already
   contributed answers, and never inside the specialist help channels. Budget
   a few weeks of genuinely helping before posting anything of your own.
   *Post:* the anti-pattern example as a discussion starter — "here are the
   six things every model gets wrong about mixed DML" — with the repo as a
   footnote.

5. **r/salesforce** — <https://www.reddit.com/r/salesforce/>.
   *Accepts:* tooling posts when they are useful first and promotional second.
   *Requires:* read the sidebar rules before posting; subreddit moderators set
   their own self-promotion policy, disclosure of affiliation is expected, and
   Reddit's general guidance is the 90/10 participation ratio
   (<https://redship.io/blog/reddit-self-promotion-rules>).
   *Post:* "I catalogued the Salesforce mistakes LLMs make, per topic" with
   three real anti-patterns inline and the link at the bottom. The post should
   stand alone if nobody clicks.

6. **Trailblazer Community** —
   <https://trailhead.salesforce.com/trailblazer-community>, group directory
   at <https://trailhead.salesforce.com/trailblazer-community/groups>.
   *Accepts:* posts inside topic groups (Developer, DevOps, Architects) rather
   than a global feed.
   *Requires:* a Trailblazer account and membership in the relevant group;
   engagement norms are heavily Salesforce-employee-adjacent, so frame it as
   community tooling, never as a product.
   *Post:* the MCP server angle — "let your AI check the org before it
   suggests a change" — which lands better with admins than the Apex example.

7. **LinkedIn** — <https://www.linkedin.com/> (the Salesforce ecosystem lives
   there far more than on X).
   *Accepts:* anything, which is why it converts poorly unless it is specific.
   *Requires:* nothing but a post. Tag nobody in the first one.
   *Post:* a carousel or single image of the before/after code, with the
   platform rule spelled out in the caption. Repeat monthly with a different
   anti-pattern; the catalogue gives you an effectively unlimited supply.

8. **Salesforce Ben** — <https://www.salesforceben.com/write-for-us/>.
   *Accepts:* guest articles from ecosystem practitioners.
   *Requires:* an open submissions window. As of 2026-07-31 the page states
   "Submissions are closed while we work through our most recent content
   pitches" and that they "plan to open again in the summer". Treat this as
   opportunistic — check back rather than plan around it.
   *Post:* a long-form piece on AI-generated Salesforce code failure modes,
   with the library as the evidence base rather than the subject.

9. **TDX** — <https://www.salesforce.com/tdx/>. The annual developer event is
   the one in-person beat worth planning for: a community session or a
   lightning talk reaches the exact audience, but the call for participation
   opens months ahead and needs a track record. Aim at the next cycle, using
   whatever traction steps 1–8 produce as the submission's evidence.

---

## Sequencing and what "working" looks like

Steps 0–2 are a single afternoon and unblock everything else. Step 3 is now a
verification-and-submission task rather than a build — the manifests exist —
but a directory review has its own latency, so do not let it block steps 4–9.

- **After Step 0:** the repository description, a v1.0.0 release, and a social
  preview all agree with each other and with `scripts/check_doc_counts.py`.
- **After steps 1–2:** SfSkills is discoverable by someone who never visits
  GitHub — searchable in the MCP registry and visible in the skills ecosystem.
- **After steps 4–7:** the measure is issues and questions, not stars. A
  stranger opening an issue about a specific skill is worth more than fifty
  stars, because it proves someone read past the README.
- **Before Step 8 or 9:** you need a story with numbers in it — "N teams
  installed it, here is what it caught" — which none of the earlier steps
  produce on their own. Do not pitch until you have one.

The failure mode to avoid: posting the skill count. It reliably produces
"can't the model already do this?", which is the argument you cannot win in a
comment thread. Post the wrong code and the right code, side by side, and let
the reader decide whether their assistant would have caught it.

---

## Channels deliberately left off the list

- **Product Hunt / Hacker News.** Both reward novelty over usefulness, and the
  audience overlap with working Salesforce practitioners is small. A "Show HN"
  with 9 stars behind it converts a one-shot spike into nothing.
- **X / Twitter.** The Salesforce ecosystem's centre of gravity moved to
  LinkedIn and Discord. Cross-post if it is free; do not invest there.
- **Paid promotion of any kind.** There is no funnel to send traffic into yet.
  Spend the effort on getting the Step 3 plugin listed and on shrinking the
  first-run path instead — a working one-command install is worth more than
  any amount of reach.
- **The AppExchange** (<https://appexchange.salesforce.com/>). This is a
  developer-tooling library, not a packaged Salesforce app; there is nothing
  to list.

---

*Verified on 2026-07-31.*
