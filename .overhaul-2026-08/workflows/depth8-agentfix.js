export const meta = {
  name: 'sfskills-agent-apex-fix',
  description: 'Fix the Apex agents that emit non-compiling code: the API 67 security-idiom regression, fabricated Apex API names, and the canonical trigger template that does not deploy',
  phases: [{ title: 'Build' }, { title: 'QA' }, { title: 'Review' }],
}

const REPO = '/Users/pranavnagrecha/VS Code/Personal/SfSkills'

const COMMON = `
REPO: ${REPO}   (cd here first; the path has a space — quote it)
Branch: overhaul/2026-08-01-checkpoint. Do NOT create branches, commit, or push.
Today is 2026-08-01 (Summer '26). 'timeout' does NOT exist on this macOS shell.

*** MEMORY RULE — OTHER WAVES ARE RUNNING ON A 16 GB MACHINE ***
DO NOT run scripts/search_knowledge.py (~2.9 GB), skill_sync.py or build_index.py.
validate_repo.py --agents is cheap and IS allowed. WebSearch/WebFetch cost no local memory.

WHY THIS EXISTS. A deep review of all 48 run-time agent playbooks found that the Apex agents —
the most-used agents in the library — instruct the model to emit code that DOES NOT COMPILE on
a current org, and to emit Apex API names that DO NOT EXIST. These agents are the product: a
user runs /refactor-apex or /gen-tests and receives this as finished work.

VERIFY EVERY CLAIM BELOW AGAINST OFFICIAL SALESFORCE DOCS BEFORE ACTING. The review is a lead,
not proof, and a wrong "fix" here is as damaging as the defect. In particular, confirm the API
version behaviour yourself against the Summer '26 (API 67.0) Apex Developer Guide / release
notes before rewriting any security idiom.
`

const ITEMS = [
  {
    id: 'apex-security-idiom',
    title: 'Correct the Apex security idiom for API 67 and remove fabricated Apex API names',
    owns: [
      'agents/apex-refactorer/AGENT.md',
      'agents/soql-optimizer/AGENT.md',
      'agents/security-scanner/AGENT.md',
      'agents/apex-builder/AGENT.md',
      'agents/test-class-generator/AGENT.md',
      'agents/trigger-consolidator/AGENT.md',
      'agents/_shared/AGENT_CONTRACT.md',
    ],
    goal: `FIX 1 — THE SECURITY IDIOM (verify first, then apply).
The review states that Summer '26 / API 67.0 makes SOQL/SOSL/DML/Database methods default to
USER MODE, and that 'WITH SECURITY_ENFORCED is no longer supported, use WITH USER_MODE instead'.
It also states user mode GA'd in Spring '23 at API 58.0, so soql-optimizer's 'API 61+' gate is
wrong.

VERIFY BOTH FACTS against official Salesforce documentation with WebFetch BEFORE editing. If
the "no longer supported" claim is softer than stated (e.g. deprecated-but-accepted), say so
and write the accurate, version-qualified guidance instead of a blanket replacement. Getting
this subtly wrong in six agents is worse than leaving it.

Then, per the verified reality:
 - apex-refactorer Step 2, soql-optimizer Steps 2-3, security-scanner Step 3 currently
   prescribe or accept WITH SECURITY_ENFORCED. Correct them.
 - security-scanner SCORES the presence of WITH SECURITY_ENFORCED as clean. It needs a finding
   for that idiom on a class whose apiVersion is 67.0+. That inversion — a security scanner
   green-lighting an unsupported security construct — is the worst single defect found.
 - Remove soql-optimizer's incorrect 'API 61+' gate.
 - apex-builder Step 3 is reportedly already correct; verify and leave it alone if so.
 - Put the canonical rule ONCE in agents/_shared/AGENT_CONTRACT.md as a
   'security idiom by API version' block, and have the Apex agents reference it rather than
   each restating it. Six copies of a version-sensitive fact is how this drifted.

FIX 2 — FABRICATED APEX API NAMES. Each of these appears in an agent's Plan steps and would be
handed to a user as finished code. Verify the real name against templates/apex/**/*.cls (grep
for the actual method signatures) and/or official docs, then correct every occurrence:
 - 'stripInaccessibleFields' — no such API. The real one is
   Security.stripInaccessible(AccessType, records).getRecords(). Appears in ~3 agents.
 - 'SecurityUtils.requireUpdateable' — the template method is requireUpdatable (spelling).
   Confirm the actual spelling in templates/apex/SecurityUtils.cls before changing anything.
 - test-class-generator invents: TestDataFactory.accounts(200),
   .contacts(n, parentAccount), MockHttpResponseGenerator.forEndpoint(...),
   TestUserFactory.standardUser(). NONE exist in templates/apex/tests/. Read those template
   files and replace with the REAL signatures. This agent was graded NO by the reviewer — its
   output currently cannot compile.
 - apex-builder invents Test.setMock(ConnectApi.ConnectApi.class, ...). Correct it.

FIX 3 — CONTRACT RULE. Add a rule to AGENT_CONTRACT.md: any Apex identifier appearing in a Plan
step must be copied verbatim from the cited template or official documentation, never written
from memory. Note in the rule that this is mechanically checkable by grepping Plan-step
identifiers against templates/apex/**/*.cls, so a future validator can enforce it.

FIX 4 — AGENT_RULES.md is missing from the Mandatory Reads of five of these six agents even
though AGENT_CONTRACT.md section 3 says the section 'Always includes AGENT_RULES.md'. Either
add it where missing or correct the contract sentence — decide which is right and make them
agree. Do not leave a documented rule that nothing follows.

Keep edits surgical. Do NOT restructure the agents or touch unrelated sections.`,
  },
  {
    id: 'trigger-template-deploys',
    title: 'Make the canonical trigger framework actually deployable',
    owns: [
      'templates/apex/cmdt/',
      'templates/apex/TriggerControl.cls',
      'templates/apex/README.md',
    ],
    goal: `The canonical trigger framework that two agents route users to DOES NOT DEPLOY AS SHIPPED.

VERIFY, then fix:
 1. templates/apex/cmdt/Trigger_Setting__mdt.object-meta.xml declares the CustomObject with
    ZERO field definitions, but templates/apex/TriggerControl.cls (~line 41) queries
    Object_API_Name__c, Handler_Class__c and Is_Active__c. Read both files and confirm.
    Fix by adding the missing CustomField metadata files (or field definitions) so the object
    the class queries actually exists. Match the real Metadata API shape for a CustomMetadata
    type — check an existing correct example in the repo first if one exists, and verify the
    field types against what TriggerControl.cls actually does with each value.
 2. TriggerControl.cls calls FeatureManagement.checkPermission('TriggerControl_BypassAll') for
    a Custom Permission that exists NOWHERE in the repo. Either ship the CustomPermission
    metadata alongside it, or document prominently that the consumer must create it — and make
    the code degrade safely if it is absent (checkPermission on a non-existent custom
    permission should not break the bypass path; verify what it actually returns).
 3. Check the rest of templates/apex/ for the same class of defect: a .cls that references
    metadata the template set does not ship. Report anything else you find.

This matters because AGENT_CONTRACT rule 2 tells agents to prefer templates over freestyling —
so a broken template is worse than no template: it is authoritatively wrong.

Do NOT edit any agents/ file — the concurrent item owns those.`,
  },
]

const BUILD_SCHEMA = {
  type: 'object',
  properties: {
    item_id: { type: 'string' },
    verification_results: { type: 'array', description: 'each claim checked against official docs/templates, with the verdict and URL', items: { type: 'string' } },
    files_changed: { type: 'array', items: { type: 'object', properties: { path: { type: 'string' }, action: { type: 'string' }, summary: { type: 'string' } }, required: ['path', 'action', 'summary'] } },
    claims_refuted: { type: 'array', description: 'review claims that did NOT hold up — leaving content alone is a valid outcome', items: { type: 'string' } },
    real_api_names_used: { type: 'array', description: 'the corrected identifiers and where you sourced each', items: { type: 'string' } },
    not_done: { type: 'array', items: { type: 'string' } },
  },
  required: ['item_id', 'verification_results', 'files_changed', 'claims_refuted', 'real_api_names_used', 'not_done'],
}

const QA_SCHEMA = {
  type: 'object',
  properties: {
    item_id: { type: 'string' },
    verdict: { type: 'string', enum: ['PASS', 'PASS_WITH_ISSUES', 'FAIL'] },
    fabricated_names_gone: { type: 'string', description: 'grep proof across agents/ and templates/' },
    identifiers_exist: { type: 'string', description: 'proof every Apex identifier now referenced exists in templates or official docs' },
    defects: { type: 'array', items: { type: 'object', properties: { severity: { type: 'string', enum: ['blocker', 'major', 'minor'] }, file: { type: 'string' }, description: { type: 'string' } }, required: ['severity', 'file', 'description'] } },
    agents_gate_result: { type: 'string' },
  },
  required: ['item_id', 'verdict', 'fabricated_names_gone', 'identifiers_exist', 'defects', 'agents_gate_result'],
}

const REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    verdict: { type: 'string', enum: ['APPROVE', 'APPROVE_WITH_COMMENTS', 'REQUEST_CHANGES'] },
    api_version_claim_correct: { type: 'string', description: 'your independent verdict on the API 67 / WITH USER_MODE claim, with the official source' },
    new_fabrications: { type: 'array', items: { type: 'string' } },
    would_it_compile: { type: 'string', description: 'judgement: would code produced by these playbooks now compile on a current org' },
    required_changes: { type: 'array', items: { type: 'string' } },
  },
  required: ['verdict', 'api_version_claim_correct', 'new_fabrications', 'would_it_compile', 'required_changes'],
}

phase('Build')
log('Fixing the Apex agents: API 67 security idiom, fabricated API names, undeployable trigger template.')

const builds = await parallel(ITEMS.map((item) => () => agent(`${COMMON}

YOU ARE THE BUILDER for "${item.id}".

ITEM: ${item.title}
FILES YOU MAY TOUCH (strict):
${item.owns.map((o) => '  - ' + o).join('\n')}

GOAL:
${item.goal}

Record every verification in verification_results with the source you actually opened. If a
claim does not hold up, put it in claims_refuted and leave the content alone — that is a
success, not a failure.`, { label: `build:${item.id}`, phase: 'Build', schema: BUILD_SCHEMA, effort: 'high' })
  .then((build) => ({ item, build }))))

phase('QA')

const qas = await parallel(builds.filter(Boolean).map((ctx) => () => agent(`${COMMON}

YOU ARE THE QA AGENT for "${ctx.item.id}". TEST; MODIFY NOTHING.

BUILDER CLAIMS: ${JSON.stringify(ctx.build, null, 2).slice(0, 18000)}

1. PROVE THE FABRICATED NAMES ARE GONE, repo-wide:
     grep -rn "stripInaccessibleFields" agents/ templates/ skills/ | wc -l
     grep -rn "requireUpdateable" agents/ templates/ | wc -l
     grep -rn "TestDataFactory.accounts(\\|MockHttpResponseGenerator.forEndpoint\\|TestUserFactory.standardUser" agents/ | wc -l
     grep -rn "WITH SECURITY_ENFORCED" agents/ | head -20
   Paste all output.
2. EVERY Apex identifier now referenced in the touched agents must actually exist. For each,
   grep templates/apex/**/*.cls for the real signature, or verify against official docs with
   WebFetch. An identifier that exists in neither is a BLOCKER — that is the exact defect this
   wave is fixing.
3. TEMPLATE DEPLOYABILITY: confirm every field TriggerControl.cls queries now has a
   corresponding metadata file, and that field types match how the class uses them. List the
   field files and the query line side by side.
4. python3 scripts/validate_repo.py --agents (cheap) — paste the result. Pre-existing
   doc-count ERRORs are expected; new errors are blockers.
5. git status --short to confirm scope.`, { label: `qa:${ctx.item.id}`, phase: 'QA', schema: QA_SCHEMA, effort: 'high' })
  .then((qa) => ({ ...ctx, qa }))))

phase('Review')

const review = await agent(`${COMMON}

YOU ARE THE REVIEWER for both items. Modify nothing.

RESULTS: ${JSON.stringify(qas.filter(Boolean), null, 2).slice(0, 30000)}

1. Read the real diff: cd "${REPO}" && git diff -- agents/ templates/
2. THE LOAD-BEARING QUESTION: independently verify the API 67 / WITH USER_MODE claim against
   official Salesforce documentation. Open the page yourself. This wave rewrote the security
   idiom across several agents on the strength of it — if the claim is wrong or overstated,
   this wave made things worse and it is REQUEST_CHANGES. Be specific about what is supported,
   deprecated, or unsupported at which API version.
3. Check no NEW fabricated identifier was introduced. Every Apex name in the diff must trace to
   a template file or an official doc page. Verify the important ones yourself.
4. Judge would_it_compile honestly: if a user ran these playbooks today against a current org,
   would the emitted Apex compile? That is the bar this wave exists to clear.
5. Confirm the security-scanner change actually inverts correctly — it must now FLAG the
   unsupported idiom rather than score it clean.`, { label: 'review:agentfix', phase: 'Review', schema: REVIEW_SCHEMA, effort: 'high' })

log(`Agent-fix review: ${review?.verdict} | compiles: ${review?.would_it_compile?.slice(0, 80)}`)

return { builds: builds.filter(Boolean).map((b) => b.build), qa: qas.filter(Boolean).map((q) => q.qa), review }
