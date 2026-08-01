export const meta = {
  name: 'sfskills-max-build-specs',
  description: 'Turn every research finding into write-ready content and specs: exact replacement text, test suites, eval cases, retrieval routing design, and the remaining domain verifications',
  phases: [{ title: 'Specify' }],
}

const REPO = '/Users/pranavnagrecha/VS Code/Personal/SfSkills'
const SCRATCH = '/private/tmp/claude-501/-Users-pranavnagrecha-VS-Code-Personal-SfSkills/c190ea2f-6abb-4296-8a86-59fc95885f09/scratchpad'
const OUT = SCRATCH + '/max2'

const COMMON = `
REPO: ${REPO}   (cd here first; the path has a space — quote it)
Today is 2026-08-01 (Summer '26, API 67.0). 'timeout' does NOT exist on this macOS shell.

YOU ARE READ-ONLY with respect to the repo. Create/edit/delete NOTHING under ${REPO}.
Write your deliverable as files under ${OUT}/ (mkdir -p it) AND return it in the schema.

*** MEMORY RULE — MANY AGENTS IN PARALLEL ON A 16 GB MACHINE ***
DO NOT run scripts/search_knowledge.py (~2.9 GB), validate_repo.py, skill_sync.py or
build_index.py. grep/ls/sed/awk/file reads only. WebSearch/WebFetch cost no local memory.

RESEARCH ALREADY BANKED — read what you need from these instead of re-deriving:
  ${SCRATCH}/depth-plan.json      167 practices, 6 domains, 140 mapped absorptions w/ targets
  ${SCRATCH}/wide-research.json   245 practices, 10 areas, 94 uncovered, 62 stale findings
  ${SCRATCH}/fabhunt.json         76 confirmed fabrications, 4 security-severity
  ${SCRATCH}/agent-review.json    all 48 run-time agents graded + top improvement each
  ${SCRATCH}/contradictions.json  cross-skill + self-contradictions + decision-tree defects
  ${SCRATCH}/EVIDENCE.md          orchestrator-measured facts
  ${SCRATCH}/HANDOFF.md           full state + recommended order

ESTABLISHED FACTS (do not re-litigate):
- Failure signature is number-RELABELLING: a REAL Salesforce number on the WRONG dimension.
  Re-read the source page; never just swap a digit.
- Several specific-looking numbers are CORRECT (131,021-char Data Cloud SQL limit, 9,950
  segments). Never flag one without opening the page.
- \`WITH SECURITY_ENFORCED\` is REMOVED at API 67.0; user mode is the default; user mode GA'd
  Spring '23 = API 57.0.
- Corpus gaps, measured: only 11.0% of skills quote a verbatim platform error string; only
  8.4% name the exact gating licence/permission. Those two are the highest-leverage additions.
- Retrieval: coverage "NONE" is fixed (23.3% -> 4.5%) but ROUTING is weak (held-out Hit@1
  ~35.7%). A single search costs ~2.9 GB / ~6 s — a product defect in its own right.

YOUR JOB IS TO PRODUCE WRITE-READY OUTPUT, not advice. A future builder should be able to
apply your deliverable with near-zero judgement. Exact file paths, exact replacement text,
exact commands. Where you cannot be certain, say so explicitly rather than guessing.
`

const SCHEMA = {
  type: 'object',
  properties: {
    area: { type: 'string' },
    deliverable_path: { type: 'string', description: 'the file you wrote under the scratchpad' },
    ready_to_apply: {
      type: 'array',
      description: 'each item a builder can apply verbatim',
      items: {
        type: 'object',
        properties: {
          target_file: { type: 'string' },
          action: { type: 'string', enum: ['replace', 'insert', 'delete', 'create'] },
          locator: { type: 'string', description: 'line number or the exact anchor text to find' },
          old_text: { type: 'string' },
          new_text: { type: 'string' },
          justification: { type: 'string', description: 'the official source that settles it' },
          risk: { type: 'string', enum: ['low', 'medium', 'high'] },
        },
        required: ['target_file', 'action', 'locator', 'new_text', 'justification', 'risk'],
      },
    },
    open_questions: { type: 'array', items: { type: 'string' } },
    notes: { type: 'string' },
  },
  required: ['area', 'deliverable_path', 'ready_to_apply', 'open_questions', 'notes'],
}

const AREAS = [
  { k: 'security-fixes', p: `Produce EXACT replacement text for the 4 security-severity findings in fabhunt.json. For each: read the current file, verify the correction against official Salesforce docs yourself with WebFetch, then write the precise old_text -> new_text. The four are: (1) security/encrypted-field-query-patterns:85 claiming "View Encrypted Data" gates plaintext — it does not; Shield is transparent to anyone with field read access, and plaintext is restricted via FLS, not that permission. (2) apex/apex-encoding-and-crypto:59 listing HmacSHA384 — Apex Crypto.generateMac supports only hmacMD5/hmacSHA1/hmacSHA256/hmacSHA512. (3) security/guest-user-security — the guest access model is inverted in ~5 places; guest OWD is Private for every object and cannot be changed, access is granted exclusively via guest user sharing rules, NOT by setting OWD to Public Read Only. (4) agentforce/data-cloud-vector-search-dev:31 — fabricated Trust Layer audit endpoint; the real path is the Data Cloud audit DMOs (GenAIGatewayRequest__dlm etc). ALSO write the anti-pattern entry for each so a model cannot regenerate the error — full diagnostic quad: what the LLM generates / why it happens / correct version / mechanically-checkable detection hint.` },
  { k: 'executable-fab', p: `Fix the fabrications that became EXECUTABLE. (1) skills/apex/long-running-process-orchestration/scripts/check_long_running_process_orchestration.py hard-codes the false "@future cannot be called from a Queueable" rule — it will flag CORRECT code as wrong. Read the script, verify the real rule against official docs (there is a documented allocation of 50 @future calls from a Queueable), and write the exact corrected code. (2) skills/apex/dynamic-apex ships a template asking reviewers to assert "no LimitException from describe calls" — that limit was REMOVED, so the condition cannot occur; write the corrected checklist text. (3) SWEEP FOR MORE: grep every skills/*/*/scripts/check_*.py for hard-coded Salesforce facts (limits, error strings, API names) and report any other checker encoding a claim that a prior sweep flagged. A wrong checker is worse than wrong prose because it fires automatically.` },
  { k: 'cpq-lifecycle', p: `Produce the CPQ deprecation notices. Salesforce CPQ is end-of-sale to new customers; ~5 skill packages plus ~380 SBQQ__ references present it as current. VERIFY the exact lifecycle status, the effective date, the successor product's CURRENT official name, and — critically — that end-of-sale is NOT end-of-support (existing orgs remain supported for years). Then write the exact notice block to insert near the top of each affected SKILL.md, plus the decision guidance: NEW implementation -> successor; EXISTING org -> this skill still applies. Identify the affected files precisely (ls skills/*/ | grep -i cpq; grep -rl SBQQ__ skills/ | head -30). No alarmism: a notice that scares an existing CPQ team into a migration they do not need is its own defect.` },
  { k: 'tooling-tests', p: `Write the actual test suite for the build tooling. 16,866 lines across scripts/ and pipelines/ have ZERO unit tests. Read pipelines/ranking.py, lexical_index.py, frontmatter.py, validators.py, similarity.py, chunker.py and scripts/check_doc_counts.py, then WRITE COMPLETE, RUNNABLE stdlib-unittest test files as your deliverable (full file contents in new_text, ready to drop into tests/). Cover: aggregate_skill_scores ordering and the max_score-vs-cumulative distinction; the name/description match bonus maths including empty-query and unknown-skill paths; that the OPTIONAL metadata argument preserves POSITIONAL backwards compatibility (the MCP server calls it positionally); FTS5 sanitisation of +, %, *, quotes, parens; frontmatter parse/roundtrip; each validator gate's pass AND fail behaviour on small synthetic fixtures in tmp dirs. Do NOT depend on the real 1,027-skill corpus — hermetic fixtures only. Also write .github/workflows/tests.yml running the repo suite plus 'python3 -m unittest discover -s tests' for the MCP suite (233 of 248 MCP tests currently never run).` },
  { k: 'retrieval-routing', p: `DESIGN the fix for retrieval routing. Held-out Hit@1 is ~35.7% — the "no coverage" bug is fixed but the wrong skill often ranks first. Read pipelines/ranking.py, pipelines/lexical_index.py, scripts/search_knowledge.py, config/retrieval-config.yaml and evals/measurement/run_heldout.py + heldout-queries.json. Analyse the failure MECHANISMS from the query set (you may read heldout-queries.json and reason about which queries would fail and why — do NOT run the benchmark, it costs 2.9 GB). Known diagnosis: chunk-level lexical scoring cannot distinguish "this skill is ABOUT X" from "this skill MENTIONS X"; a name/description match signal already exists and helped; the FTS5 tokenizer OR-joins every token including stopwords, flooding the 30-row window on conversational queries. REFUTED, do not pursue: vertical skills outranking generic ones (4.0% vs a 10.5% baseline). Deliver a ranked, specific set of code changes with the exact functions to modify, plus the measurement protocol to validate each ONE AT A TIME against both the fixtures (sacred floor) and the held-out set.` },
  { k: 'retrieval-memory', p: `DESIGN the retrieval memory fix. A single search peaks at 2.91 GB (or 3.84 GB with embeddings) and takes 6-28 s, which locks out anyone on an 8 GB laptop — a product defect, not just an ops nuisance. Root cause: scripts/search_knowledge.py load_chunks() reads the entire 126 MB vector_index/chunks.jsonl into a Python dict merely to fetch snippets for the ~30 rows the lexical pass returned; load_embeddings() does the same for a 535 MB file. Read those functions plus pipelines/lexical_index.py and pipelines/sync_engine.py (which produces the artifacts). Deliver a concrete design with exact code: candidates are (a) storing chunk text in the existing lexical.sqlite FTS5 DB and reading snippets by chunk_id, (b) a byte-offset index chunk_id->offset built at index time then seek/read only what is needed, (c) mmap. Pick one, justify it, and write the actual implementation. It MUST preserve behaviour exactly, keep aggregate_skill_scores' positional signature working for the MCP server, and state clearly whether a full index rebuild is required (and if so, that build_index.py must produce the new format).` },
  { k: 'plugin-complete', p: `Complete the Claude Code plugin packaging. Current state: .claude-plugin/plugin.json declares ONLY "skills" — no "agents" and no "commands" key — while its own description advertises "48 run-time agents and 66 slash commands", and .claude/commands/ (66 files) is not tracked at all. So the plugin is NOT shippable. RESEARCH the current Claude Code plugin manifest schema with WebSearch/WebFetch against Anthropic's official docs — do not guess field names — and cite the doc URL. Read .claude-plugin/plugin.json, .claude-plugin/marketplace.json, scripts/build_plugin.py, .gitignore (note it now un-ignores .claude/agents/ and .claude/skills/) and docs/installing-the-plugin.md. Deliver the exact corrected plugin.json and marketplace.json contents, the .gitignore change needed to track .claude/commands/, the scripts/build_plugin.py changes so this cannot drift again, and the exact install command a user runs. Also give the verification steps that would PROVE the plugin path works (as distinct from project-local loading, which is what was previously mistaken for proof).` },
  { k: 'verify-flow-devops', p: `VERIFICATION SWEEP: skills/flow (63) and skills/devops (70). Extract and verify numeric limits, error strings, API identifiers, sf CLI command syntax (heavily renamed from sfdx — flag stale forms), test-level names and the coverage rule. Known context: flow already had inverted mechanisms found (subflow version resolution, a non-existent fault mechanism, a fabricated AllOrNone partial-success claim) so treat mechanism claims with suspicion; and order-of-execution step numbers are stale corpus-wide. Verify against official docs, report CORRECT verdicts too, and produce exact old->new replacement text for what is wrong.` },
  { k: 'verify-integration-arch', p: `VERIFICATION SWEEP: skills/integration (61) and skills/architect (104). Extract and verify: API limits, Platform Event and CDC delivery allocations and retention windows, replay-ID semantics, composite API sub-request caps, OAuth flow names, Named Credential field names, org-wide 24-hour limits, edition-specific caps. Note architect was measured as having 0 uncovered practices but 10 stale/wrong findings — so this is a CORRECTION sweep, not an addition sweep. Verify against official docs, report CORRECT verdicts too, and produce exact old->new replacement text.` },
  { k: 'docs-readme', p: `AUDIT the human-facing documentation for accuracy and produce corrected text. Read README.md and every docs/*.md added this session (README, getting-started, architecture, faq, troubleshooting, glossary, installing, installing-the-plugin, worked-example-*, positioning, comparison, go-to-market). CHECK EVERY CLAIM: run the commands they tell a user to run (cheap ones only — never build_index/skill_sync/validate_repo/search_knowledge) and confirm counts with 'python3 scripts/check_doc_counts.py'. Known corrections needed: the install block should call scripts/bootstrap.py (measured 9 s cold), NOT build_index.py which leaves 1,029 modified tracked files on a clean clone; a documented "15+ minutes / 800 MB" figure is false (real: ~9 s, ~292 MB) because requirements.txt does not install fastembed; an asserted search score of 2.505 is really 2.350 so the doc should tell readers to assert the skill ID, not the score; CONNECT.md has 18 client sections not 24; clone is ~130 MB working tree / 29 MB .git. Produce exact old->new text for every inaccuracy you find.` },
  { k: 'mcp-review', p: `REVIEW the MCP server for correctness and shippability. Read mcp/sfskills-mcp/ (README, pyproject.toml, docs/CONNECT.md, src/sfskills_mcp/*.py, tests/). Known issues: 'pip install sfskills-mcp' resolved mcp 2.0.0 and crashed (now pinned >=1.7.0,<2.0 — verify the pin is in BOTH pyproject.toml and requirements.txt); 'sfskills-mcp-init' 404s because there are zero GitHub releases and .github/workflows/publish-mcp.yml would ship an index-less tarball because only 3 vector_index files are tracked; PyPI version drift (wheel 0.4.6 but __version__ reported 0.4.4); 233 of 248 tests never run in CI; and the MCP search path re-implements retrieval rather than importing run_search, so the two surfaces can diverge. Verify each, then deliver exact fixes: the publish workflow step that builds the index before bundling, the smoke test that would have caught the unbounded pin, and the code change to unify the retrieval path.` },
  { k: 'omnistudio-specs', p: `Turn the OmniStudio research into write-ready content. wide-research.json shows OmniStudio had 26 of 27 practices UNCOVERED — the single biggest opportunity in the library, and it is also the thinnest domain (24.7 KB median vs 40 KB). Read that file's OmniStudio area, then for EACH uncovered practice produce the actual content to insert: which existing skills/omnistudio/<slug> package and which file (SKILL.md / references/gotchas.md / references/llm-anti-patterns.md / references/examples.md), and the exact prose. Verify every target path exists with ls. Anti-pattern entries must carry the full quad: what the LLM generates / why it happens / the correct version / a mechanically-checkable detection hint. RESPECT the ~50 KB per-package ceiling — measure each target (find <dir> -name '*.md' -exec cat {} + | wc -c) and say what the post-insert size would be.` },
]

phase('Specify')
log(`Max spec wave: ${AREAS.length} write-ready deliverables in parallel.`)

const res = await parallel(AREAS.map((a) => () => agent(`${COMMON}

YOUR AREA: ${a.k.toUpperCase()}

${a.p}

Write your full deliverable to ${OUT}/${a.k}.md as you go (so nothing is lost if this run is
interrupted), and return the structured summary. Populate ready_to_apply with items a builder
can apply verbatim — exact target_file, exact locator, exact new_text, and the official source
that justifies it. Mark risk honestly: 'high' means a human should review before applying.`,
  { label: `spec:${a.k}`, phase: 'Specify', schema: SCHEMA, effort: 'high' })))

const good = res.filter(Boolean)
const items = good.flatMap((r) => r.ready_to_apply || [])
log(`${good.length}/${AREAS.length} deliverables. ${items.length} ready-to-apply items (${items.filter((i) => i.risk === 'low').length} low-risk).`)

return {
  deliverables: good.map((r) => ({ area: r.area, path: r.deliverable_path, count: (r.ready_to_apply || []).length, notes: r.notes, open: r.open_questions })),
  ready_to_apply: items,
  totals: { areas: good.length, items: items.length, low_risk: items.filter((i) => i.risk === 'low').length, high_risk: items.filter((i) => i.risk === 'high').length },
}
