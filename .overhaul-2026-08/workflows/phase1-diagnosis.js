export const meta = {
  name: 'sfskills-phase1-diagnosis',
  description: 'Ten-lens read-only diagnosis of the SfSkills library: corpus, agents, docs, distribution, tooling, retrieval, evals, competitive landscape, platform coverage, and end-user journey',
  phases: [
    { title: 'Diagnose' },
    { title: 'Adversarial check' },
  ],
}

const REPO = '/Users/pranavnagrecha/VS Code/Personal/SfSkills'

const GROUND_RULES = `
REPO: ${REPO}
You are a READ-ONLY diagnostician. Do NOT create, edit, or delete any file in the repo.
You MAY write scratch notes only under /private/tmp/claude-501/-Users-pranavnagrecha-VS-Code-Personal-SfSkills/c190ea2f-6abb-4296-8a86-59fc95885f09/scratchpad/ if you need them.

EVIDENCE DISCIPLINE (this is the single most important rule):
- This repo has 1027 skills. Prior agents have HALLUCINATED "no skill covers X" and been wrong twice.
- You may NOT claim anything is missing/absent/uncovered unless you ran a verification command and can paste its literal output.
- The verification command for skill coverage is:
    cd "${REPO}" && python3 scripts/search_knowledge.py "<topic>"
  and/or:
    ls skills/*/ | grep -i "<term>"
    grep -ril "<term>" skills/*/*/SKILL.md | head
- For every gap you report, populate evidence_command and evidence_output with the REAL command and its REAL first ~15 lines of output. If you did not run a command, set severity to "UNVERIFIED" and say so.
- Counts must come from commands you actually ran, not estimates.

CONTEXT — what this repo is:
SfSkills / AwesomeSalesforceSkills is a Salesforce knowledge layer for AI coding assistants (Claude Code, Cursor, Windsurf, Aider, Codex, plus its own MCP server).
It is NOT a Salesforce app. It ships: skills/ (1027 human-authored skill packages), agents/ (75 AGENT.md: 47 active runtime + 14 build-time + 14 deprecated aliases), commands/ (65 slash-command wrappers), templates/ (canonical Apex/LWC/Flow/Agentforce building blocks), standards/ (decision trees, authoring contracts, validation gates), knowledge/, evals/ (golden P0 cases + agent baselines), registry/ + vector_index/ (generated retrieval artifacts), scripts/ + pipelines/ (build and validation tooling), mcp/sfskills-mcp/ (38-tool MCP server), exports/ (per-AI-tool export targets).
Read CLAUDE.md and AGENT_RULES.md at the repo root first — they define canonical rules.

THE OWNER'S GOAL: any Salesforce practitioner should be able to install this and have their AI assistant produce genuinely expert Salesforce work. The library exists to give an LLM depth on each topic that its general training does not have. The owner believes the product is strong technically but weak on structure, documentation, packaging and marketing, and suspects there are real gaps in both skills and agents.

OUTPUT: return ONLY the structured object. Be specific and actionable. A gap like "documentation could be better" is worthless; "there is no single getting-started path — a new user hits a 540-line README and 3 competing entry docs (X, Y, Z) with no ordering" is useful.
Rank your gaps most-severe first. Aim for 6-12 high-quality gaps, not 30 shallow ones.
`

const DIAGNOSIS_SCHEMA = {
  type: 'object',
  properties: {
    lens: { type: 'string' },
    summary: { type: 'string', description: '3-6 sentence honest verdict on this lens' },
    metrics: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          name: { type: 'string' },
          value: { type: 'string' },
          how_measured: { type: 'string', description: 'the exact command run' },
        },
        required: ['name', 'value', 'how_measured'],
      },
    },
    strengths: {
      type: 'array',
      items: {
        type: 'object',
        properties: { claim: { type: 'string' }, evidence: { type: 'string' } },
        required: ['claim', 'evidence'],
      },
    },
    gaps: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string', description: 'kebab-case stable id' },
          title: { type: 'string' },
          severity: { type: 'string', enum: ['P0', 'P1', 'P2', 'UNVERIFIED'] },
          what_is_missing: { type: 'string' },
          evidence_command: { type: 'string' },
          evidence_output: { type: 'string', description: 'literal output, first ~15 lines' },
          why_it_matters: { type: 'string', description: 'impact on the end user of the library' },
          proposed_fix: { type: 'string', description: 'concrete deliverable: exact files/dirs to create or change' },
          effort: { type: 'string', enum: ['S', 'M', 'L'] },
        },
        required: ['id', 'title', 'severity', 'what_is_missing', 'evidence_command', 'evidence_output', 'why_it_matters', 'proposed_fix', 'effort'],
      },
    },
  },
  required: ['lens', 'summary', 'metrics', 'strengths', 'gaps'],
}

const LENSES = [
  {
    key: 'corpus-quality',
    prompt: `LENS: SKILL CORPUS QUALITY.
Assess the 1027 skill packages as a body of work. Sample widely across ALL 11 domains (admin 253, apex 158, architect 104, data 101, lwc 82, devops 70, flow 63, integration 61, agentforce 53, security 48, omnistudio 34) — read at least 20 full SKILL.md files plus their references/.
Answer with evidence:
- Is depth uniform, or are some domains thin/boilerplate? Find the actual worst offenders by name.
- Are the references/ files (examples.md, gotchas.md, well-architected.md, llm-anti-patterns.md) genuinely useful or template-filler? Quantify: sample 20 and score.
- Do skills go "deep, deep, deep" on their topic the way the owner wants, or do they restate what an LLM already knows? Give named examples of both the best and the worst.
- Is code in examples.md real, compilable, current-API Salesforce code?
- Frontmatter/trigger quality: are 'triggers' entries natural-language phrasings a user would actually type?
- Version staleness: check 'updated' and 'salesforce-version' fields across the corpus. Salesforce is on a 3-release/year cadence and today is 2026-07-31.
Useful commands: find skills -name SKILL.md | shuf | head -20 ; grep -h "^updated:" skills/*/*/SKILL.md | sort | uniq -c | sort -rn | head ; grep -h "salesforce-version:" skills/*/*/SKILL.md | sort | uniq -c | sort -rn ; wc -c skills/*/*/references/*.md | sort -n | head -30`,
  },
  {
    key: 'agent-layer',
    prompt: `LENS: AGENT LAYER.
There are 47 active runtime agents, 14 build-time, 14 deprecated aliases. Read agents/_shared/AGENT_CONTRACT.md, AGENT_DISAMBIGUATION.md, CAPABILITY_MATRIX.md, DELIVERABLE_CONTRACT.md, RUNTIME_VS_BUILD.md, SKILL_MAP.md, then read at least 12 full AGENT.md files spanning all four tiers.
Answer with evidence:
- Do all 47 actually comply with the 8-section AGENT_CONTRACT shape? Find non-compliant ones by name (script it — do not eyeball).
- COVERAGE GAP: 1027 skills exist but only 47 runtime agents. Which large, valuable skill clusters have NO agent that can act on them? Compute this: extract every skill id cited across all agents/*/AGENT.md, diff against the full skill list, and report the biggest uncited clusters by domain. This is the highest-value output of this lens — be rigorous and paste the numbers.
- Which NEW runtime agents should exist? Propose them concretely (name, slash command, tier, primary output, the skills they'd cite), justified by the uncited clusters. Rank by user value.
- Are the deprecated aliases handled cleanly, or are they cruft that confuses users?
- Are agent inputs.schema.json files real and complete?
- Do agents overlap/conflict (two agents that would both claim the same request)?`,
  },
  {
    key: 'docs-ia',
    prompt: `LENS: DOCUMENTATION AND INFORMATION ARCHITECTURE.
Read README.md (540 lines), CLAUDE.md, AGENT_RULES.md (484 lines), AGENTS.md, CONTRIBUTING.md, SECURITY.md, BACKLOG.md, MASTER_QUEUE.md, and everything under docs/ (MIGRATION.md, QUEUE_FORMAT_PROPOSAL.md, agent-invocation-modes.md, consumer-responsibilities.md, installing-single-agents.md, multi-ai-parity.md, docs/validation/, docs/archive/, docs/release-plans/).
Answer with evidence:
- Map the ACTUAL information architecture. Where does a brand-new user land, and what is the first 15 minutes like? Walk it and report friction honestly.
- Which docs are stale, contradictory, orphaned (linked from nowhere), or duplicative? Name them. Check MASTER_QUEUE.md vs BACKLOG.yaml — CLAUDE.md says the row data moved to BACKLOG.yaml; is MASTER_QUEUE.md now a stale husk?
- Is there a tutorial / quickstart / "your first hour" path? A worked end-to-end example of a real Salesforce task done with this library? Verify by searching.
- Is there per-domain or per-role navigation, or only the 587KB generated docs/SKILLS.md?
- What is the doc set MISSING entirely (architecture overview, glossary, FAQ, troubleshooting, versioning policy, roadmap, comparison-to-alternatives, changelog discipline)?
- Propose the target IA as a concrete file tree.`,
  },
  {
    key: 'distribution',
    prompt: `LENS: DISTRIBUTION, PACKAGING AND INSTALLABILITY.
Read scripts/export_skills.py, scripts/export_agent_bundle.py, scripts/install_local_commands.py, scripts/ship_skills.py, exports/ (all 8 targets), mcp/sfskills-mcp/ (README, pyproject.toml, src, dist, docs/CONNECT.md), .github/workflows/*.yml, .claude/, CHANGELOG.md, LICENSE.
Answer with evidence:
- ACTUALLY TRY IT: run the export for at least 2 targets and inspect the output. Does it work? Is the result usable?
- What is the true install experience for each supported tool? Rate each 1-5 with reasoning. The repo is 80MB of skills plus a 535MB embeddings file and a 166MB sqlite — check what cloning actually costs a new user and whether large artifacts are committed or gitignored. Report the real clone size.
- Is the MCP server published anywhere installable (PyPI, npx, uvx, MCP registry, Claude Desktop extension/DXT)? Verify, do not assume. What is the one-command install story?
- Is there ANY release/versioning discipline (git tags, GitHub releases, semver on the whole library)? Check: git tag -l ; gh release list.
- Is Claude Code plugin/marketplace packaging present (a .claude-plugin directory, marketplace.json)? This is now the native distribution channel for Claude Code skills+agents+commands — check whether the repo has it.
- What is the single biggest friction between "user hears about this" and "user AI is using it"?`,
  },
  {
    key: 'tooling-ci',
    prompt: `LENS: BUILD TOOLING, VALIDATION AND CI.
Read all of scripts/ (46 files) and pipelines/ (12 modules), standards/validation-gates.md, .github/workflows/*, .githooks/, requirements.txt, config/*.
Answer with evidence:
- Which scripts are load-bearing vs abandoned? Check git log recency per script and whether anything references it. Name the dead ones.
- Time the critical path: how long does scripts/validate_repo.py take on 1027 skills, and does CI actually run it fully? Read .github/workflows/validate.yml and report what CI really enforces vs what it skips.
- Are there gates that SHOULD exist but do not? (e.g. link-rot checking across the 1027 skills, dead cross-reference detection, code-block syntax validation for Apex/JS in examples, frontmatter schema drift, duplicate-content detection at scale, staleness alerting.) Verify absence before claiming it.
- Is the contributor loop fast enough that a human would actually contribute? Walk CONTRIBUTING.md end-to-end.
- Is there test coverage for the tooling itself (pipelines/, scripts/)? Check for a test suite and run it.
- Report the top gaps as concrete new scripts/gates with file paths.`,
  },
  {
    key: 'retrieval-evals',
    prompt: `LENS: RETRIEVAL QUALITY AND EVALUATION.
Read config/retrieval-config.yaml, pipelines/lexical_index.py, pipelines/ranking.py, pipelines/chunker.py, scripts/search_knowledge.py, scripts/search_skills.py, scripts/query_enrichment.py, evals/ (README, framework.md, golden/, agents/, measurement/, scripts/).
Answer with evidence:
- EXERCISE THE SEARCH. Run at least 25 realistic natural-language queries a Salesforce practitioner would actually type (mix admin/dev/architect/data, mix verb-first and noun-first, include some deliberately vague). Paste the top-3 results per query. Score hit/miss yourself and report a real hit-rate. This empirical number is the most valuable thing this lens produces.
- Where does retrieval FAIL? Characterize the failure modes precisely with the failing queries.
- Eval coverage: 10 flagship skills x 3 P0 cases = 30 cases across 1027 skills, plus 15 agent baselines across 47 agents. Is that credible coverage? What would meaningful coverage look like, and what is the cheapest path to it?
- Are evals actually run in CI, or aspirational? Verify.
- Is the embeddings path on or off, and is that the right call? (Context: the owner decided to keep embeddings off; per-query latency was the binding constraint. Do not re-litigate without measured evidence — if you disagree, measure it.)`,
  },
  {
    key: 'landscape',
    prompt: `LENS: EXTERNAL LANDSCAPE AND COMPETITIVE POSITIONING. (Use WebSearch/WebFetch heavily — this lens is mostly external research.)
Research the current (2026) ecosystem of AI-assistant skill/context libraries and where a Salesforce-specific one fits:
- Anthropic's Agent Skills ecosystem: the official skills spec/format, the Claude Code plugin and marketplace mechanism, the anthropics/skills repo, and how third-party skill collections are distributed and discovered today. What conventions does a skill library need to follow in 2026 to be first-class?
- Directories/registries where a library like this SHOULD be listed to be found: Claude Code plugin marketplaces, MCP server registries/directories, awesome-lists, Cursor rules directories, skillspool.org and similar. Enumerate them concretely with URLs and their submission requirements.
- Salesforce-specific competition: forcedotcom/sf-skills (note: CC BY-NC licensed — this repo is Apache-2.0, so no code reuse, clean-room only), Salesforce's own Agentforce/DX AI tooling, Codey/Einstein for Developers, other community Salesforce AI-context repos. How does each compare on scope, depth and freshness?
- What do the BEST-marketed developer knowledge/skill repos do that this one does not? Look at concrete examples of repos with strong adoption and extract their playbook: README structure, landing page, demo GIF/video, one-command install, badges, social proof, docs site, launch channels.
- Salesforce community distribution channels specifically: Trailblazer Community, Salesforce Ben, SFXD Discord, r/salesforce, LinkedIn, Dreamforce/TDX, admin/dev podcasts and newsletters. Which are realistic and high-yield?
Deliver: a positioning statement this repo should adopt, and a ranked, concrete go-to-market list. Cite URLs in your evidence fields.`,
  },
  {
    key: 'platform-coverage',
    prompt: `LENS: SALESFORCE PLATFORM COVERAGE GAPS. (This is the highest-risk lens for hallucination — evidence discipline is mandatory.)
Map the CURRENT Salesforce platform surface (as of 2026) against what the library covers. Method:
1. First, list what exists: ls skills/*/ and read the docs/SKILLS.md table of contents. Get the real inventory into your head before searching for gaps.
2. Enumerate the platform surface systematically: core clouds (Sales, Service, Experience, Marketing Cloud including Marketing Cloud Growth/Advanced and the legacy MC Engagement, Commerce, Field Service, CPQ/Revenue Cloud including Revenue Cloud Advanced), Data Cloud, Agentforce (including Agentforce 360, agent builder, Atlas reasoning), Industries/Vertical clouds (Financial Services, Health, Public Sector, Nonprofit, Automotive, Energy and Utilities, Comms, Manufacturing, Consumer Goods, Education), platform (Apex, LWC including LWR/Lightning Web Runtime, Flow, DevOps Center, Salesforce CLI, packaging/2GP, Hyperforce, Shield, Event Monitoring, Privacy Center, MuleSoft, Tableau/Tableau Next, Slack SDK, Heroku, Einstein/Prompt Builder/Models API), and current release features (Spring '26, Summer '26).
3. For EACH candidate gap, run python3 scripts/search_knowledge.py "<topic>" AND grep the skills tree, and paste the literal output. Many "gaps" will turn out to be covered — that is a useful finding too, report the false-alarm rate.
4. Also check FRESHNESS: for topics that ARE covered, is the coverage current with 2026 Salesforce reality? Sample 6 fast-moving topics (Agentforce, Data Cloud, Revenue Cloud, Marketing Cloud Growth, DevOps Center, Einstein/Prompt Builder) and read the actual skill content; report anything that is stale or describes retired products.
Deliver a ranked list of GENUINELY missing or GENUINELY stale topics with proof. Use WebSearch to confirm current Salesforce product naming and what shipped in Spring '26 / Summer '26 — product names change constantly and the library must not teach retired names.`,
  },
  {
    key: 'end-user-journey',
    prompt: `LENS: THE END-USER JOURNEY — DOES IT ACTUALLY WORK?
Do not audit documents; SIMULATE USERS. Pick 5 concrete personas and for each, actually attempt their task using only what the repo provides, then report what happened blow-by-blow:
1. Solo Salesforce admin, non-technical, wants their AI to help build a lead-routing setup. They use Claude Code and have never seen this repo.
2. Senior Apex developer inheriting a legacy org, wants to refactor a 3000-line trigger.
3. Consultant on day 1 of a project, needs to assess an unfamiliar org.
4. Data lead planning a 5M-record migration.
5. Architect who must justify Flow vs Apex vs Agentforce to a steering committee.
For each: find the entry point, follow it, run the commands/agents, and judge the OUTPUT quality. Where does the path break, dead-end, or require knowledge the user does not have? Was the right skill/agent even discoverable?
Also test the failure mode that matters most: what happens when a user asks about something the library does NOT cover — does it degrade gracefully or confidently mislead?
This lens must produce lived friction, not theory. Quote the actual commands you ran and what came back.`,
  },
  {
    key: 'structure-hygiene',
    prompt: `LENS: REPO STRUCTURE AND HYGIENE.
The owner says "what you do not have is a proper structure." Audit the physical repo.
- Inventory every top-level directory and file and judge whether it belongs, is misplaced, or is abandoned. Pay attention to: _codex_drops/, batches/, feedback/, .planning/, .intake-reports/, .build-venv/ .qa-venv/ .smoke-venv/ .verify-venv/ (four venvs?), docs/archive/, MASTER_QUEUE.md vs BACKLOG.yaml vs BACKLOG.md, .DS_Store files.
- Check .gitignore correctness against what is actually tracked: run git ls-files | wc -l, find the largest tracked files, and report anything large/generated/junk that is committed. Specifically determine whether vector_index/embeddings.jsonl (535MB), vector_index/lexical.sqlite (166MB), vector_index/chunks.jsonl (126MB) are tracked — and what the true clone size is (check .git size and run git count-objects -vH).
- Are there stale git branches and abandoned worktrees? (git branch -a, git worktree list) Report cruft.
- Is the naming/layout consistent and predictable across skills/, agents/, commands/, templates/, standards/?
- Propose a concrete target repo structure with an explicit move/delete/keep list. Be decisive — the owner wants opinions, not a survey.`,
  },
]

phase('Diagnose')
log(`Running ${LENSES.length} independent diagnostic lenses over the SfSkills library...`)

const diagnoses = await parallel(LENSES.map((l) => () =>
  agent(GROUND_RULES + '\n\n' + l.prompt, {
    label: `diag:${l.key}`,
    phase: 'Diagnose',
    schema: DIAGNOSIS_SCHEMA,
  })
))

const good = diagnoses.filter(Boolean)
const allGaps = good.flatMap((d) => (d.gaps || []).map((g) => ({ ...g, lens: d.lens })))
log(`${good.length}/${LENSES.length} lenses returned. ${allGaps.length} candidate gaps to adversarially check.`)

phase('Adversarial check')

const toCheck = allGaps.filter((g) => g.severity === 'P0' || g.severity === 'P1' || g.severity === 'UNVERIFIED')
log(`Adversarially verifying ${toCheck.length} P0/P1/UNVERIFIED gap claims against the real repo.`)

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    gap_id: { type: 'string' },
    refuted: { type: 'boolean', description: 'true if the claim is wrong, overstated, or already satisfied somewhere in the repo' },
    confidence: { type: 'string', enum: ['HIGH', 'MEDIUM', 'LOW'] },
    reason: { type: 'string' },
    verification_command: { type: 'string' },
    verification_output: { type: 'string' },
    corrected_claim: { type: 'string', description: 'if partially right, the accurate version of the claim' },
  },
  required: ['gap_id', 'refuted', 'confidence', 'reason', 'verification_command', 'verification_output'],
}

const verified = await parallel(toCheck.map((g) => () =>
  agent(`REPO: ${REPO}
You are an adversarial verifier. Your job is to REFUTE the following claim about the SfSkills repo. Assume it is wrong until the repo proves it right.

CLAIM (from lens "${g.lens}"):
  id: ${g.id}
  title: ${g.title}
  severity claimed: ${g.severity}
  what is allegedly missing: ${g.what_is_missing}
  their evidence command: ${g.evidence_command}
  their evidence output: ${String(g.evidence_output || '').slice(0, 1200)}

DO THIS:
1. Re-run their evidence command yourself. Did it really produce that?
2. Search HARDER for the thing they say is missing — different names, different directories, generated artifacts, docs/, standards/, mcp/, exports/, scripts/, .github/. This repo is large and things hide. Use: python3 scripts/search_knowledge.py, grep -ril, find, ls.
3. Decide: is the gap REAL, ALREADY SATISFIED (refute), or OVERSTATED (refute plus give corrected_claim)?
Default to refuted=true when you are uncertain. Paste literal command output as proof.
Read-only: modify nothing.`, {
    label: `verify:${g.id}`,
    phase: 'Adversarial check',
    schema: VERDICT_SCHEMA,
    effort: 'medium',
  }).then((v) => ({ gap: g, verdict: v }))
))

const checked = verified.filter(Boolean)
const confirmed = checked.filter((c) => c.verdict && !c.verdict.refuted).map((c) => ({ ...c.gap, verification: c.verdict }))
const refuted = checked.filter((c) => c.verdict && c.verdict.refuted).map((c) => ({ id: c.gap.id, lens: c.gap.lens, title: c.gap.title, reason: c.verdict.reason, corrected: c.verdict.corrected_claim }))
const p2 = allGaps.filter((g) => g.severity === 'P2')

log(`CONFIRMED: ${confirmed.length}  REFUTED: ${refuted.length}  (P2 unverified: ${p2.length})`)

return {
  lenses: good.map((d) => ({ lens: d.lens, summary: d.summary, metrics: d.metrics, strengths: d.strengths })),
  confirmed_gaps: confirmed,
  refuted_claims: refuted,
  p2_gaps: p2,
}
