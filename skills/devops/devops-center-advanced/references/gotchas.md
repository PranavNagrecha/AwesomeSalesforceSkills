# Gotchas — DevOps Center Advanced Workflows

Non-obvious behaviours that bite teams already running DevOps Center at scale.

---

## Gotcha 1: Two Different Products Answer to "DevOps Center"

**What happens:** A runbook, a blog post, or an AI answer describes a setup step
that does not exist in your org, and the team concludes their install is broken.

**When it occurs:** Constantly, since the next-generation DevOps Center shipped.
The managed-package version is installed and configured as an app; the
next-generation version is a native platform capability with no package to
install. Salesforce documents them as separate products — *Install and Configure
DevOps Center (Managed Package)* versus *Set Up Next Generation DevOps Center* —
and they differ in source-control support, change tracking, and governance
surface.

**How to avoid:** Establish which product a piece of guidance describes before
acting on it. The strongest tell is the setup step: if it starts with installing
a package, it is the managed-package product. Anything that mentions DX
Inspector, agent governance policies, or Bitbucket is next-generation.

---

## Gotcha 2: A Commit Outside the Work-Item Branch Is Invisible to the Promotion

**What happens:** A developer merges a feature branch straight into the
integration branch. The work item that "covers" that change promotes later and
carries a partial or empty diff. The pipeline reports success. The next
environment down the line receives a different set of metadata than the one
above it.

**When it occurs:** Any time a branch that is not a work-item branch is merged
into a pipeline branch. DevOps Center's promotion model is work-item shaped —
the work item owns a branch and a set of changes, and promotion moves that
branch through the stages. Commits made outside that structure are real in git
and absent from the promotion.

**How to avoid:** Enforce the negative rule: no branch that is not a work-item
branch is ever merged into a pipeline branch. Developers keep the CLI, local
tests, and their editor — they just check out the branch DevOps Center created
rather than one of their own. Where the source-control provider supports branch
protection, encode the rule there rather than in a wiki.

---

## Gotcha 3: Flow XML Conflicts Are Not Textually Resolvable

**What happens:** Two admins edit the same flow on separate work items. The
second promotion hits a merge conflict whose diff is hundreds of lines of XML,
including canvas coordinates. Somebody resolves it by hand and the flow is
subtly wrong — a connector pointing at the wrong element, an orphaned decision
outcome — with no error at deploy time.

**When it occurs:** Any concurrent edit of the same flow. A flow version is one
XML document with element positions (`locationX`, `locationY`) embedded in it, so
even a purely cosmetic reposition produces conflict hunks that look semantically
meaningful.

**How to avoid:** Never hand-merge flow XML. Accept one side wholesale, re-apply
the other change in Flow Builder in a sandbox, and commit that result. Then
deploy to a test stage and open the flow on the canvas to confirm it is intact
before promoting further. Better: treat "who edits which flow this sprint" as a
scheduling constraint at work-item assignment time.

---

## Gotcha 4: Permission Sets and Profiles Deploy as a Full Replace

**What happens:** A work item adds three field permissions to an existing
permission set. After promotion, users have lost twenty-two permissions they had
before, and no error was raised.

**When it occurs:** Whenever the deployed `PermissionSet` XML is not a complete
superset of the target org's current state. The Metadata API treats the deployed
document as the whole truth and removes anything absent from it. A work item that
captured only the three new field permissions is a destructive change dressed as
an additive one.

**How to avoid:** This is a metadata-type hazard rather than a DevOps Center one,
but the work-item model makes it easier to hit because the commit captures a
delta. Retrieve the target org's current state, merge, and commit the merged
document. `devops/permission-set-deployment-ordering` covers the full pattern
including the ConnectedApp cross-reference case.

---

## Gotcha 5: Promotion Runs Tests in the Target Org, and Target Orgs Are Shared

**What happens:** Promotions to UAT queue behind each other and the release
window slips. The pipeline looks slow; the deploys are not.

**When it occurs:** Promotion into a stage deploys into that stage's org, and
the tests run there. On a shared UAT org with several teams promoting, the
constraint is org capacity, not pipeline throughput.

**How to avoid:** Front-load the expensive validation. Run `sf project deploy
validate` against a test stage early on every work item, and reserve the shared
org for the promotions that need it. If the contention is structural, the answer
is more stages or more orgs, not a faster pipeline. And note that slow promotion
is the root cause of most bypass culture — see Gotcha 6.

---

## Gotcha 6: An Un-Reconciled Bypass Is Reverted by the Next Normal Promotion

**What happens:** An emergency fix is deployed straight to production. Three days
later a routine promotion reverts it and the incident recurs.

**When it occurs:** Every time the bypass is applied to production only. Lower
environments do not have the change; the next promotion from a lower environment
carries the old state forward and overwrites it. Nothing warns you, because from
the pipeline's point of view the promotion is correct — it deployed exactly what
the branch contained.

**How to avoid:** Every bypass carries a mandatory reconciliation task that
cascades the change *down* the pipeline, not just a note that it happened. Do it
before the incident is closed, not in the morning. Then count bypasses monthly:
a rate that is not trending toward zero is a statement about pipeline latency,
and the fix is to make normal promotion fast enough that nobody wants the
bypass.

---

## Gotcha 7: `deploy start` Without an Explicit Test Level Inherits the Org Default

**What happens:** A deploy that passed in every lower environment fails at
production on test coverage, or runs a full test suite nobody budgeted time for.

**When it occurs:** Whenever `--test-level` is omitted. The behaviour then comes
from the target org's defaults rather than from the command, so the same command
behaves differently against different orgs — which is precisely the property a
pipeline is supposed to eliminate.

**How to avoid:** Set `--test-level` explicitly on every deploy and validate
command, in every environment. Use `sf project deploy validate` followed by `sf
project deploy quick --job-id <id>` for production so the tests run once, ahead
of the change window, and the production step is short.

---

## Gotcha 8: The Pipeline CLI Commands Are Beta

**What happens:** A team automates promotion in CI using `sf project deploy
pipeline start`, and a CLI upgrade changes flag names or behaviour mid-release.

**When it occurs:** The `sf project deploy pipeline` family — `start`,
`validate`, `quick`, `report`, `resume` — is currently documented as beta.
Beta commands can change without the deprecation cycle a GA command gets.

**The failure that comes first, though, is not instability — it is absence.**
These subcommands are not in the base CLI. They ship in
`@salesforce/plugin-devops-center`, itself an optional beta plugin, so a CI
runner that installs only `@salesforce/cli` gets "command not found." Add
`sf plugins install @salesforce/plugin-devops-center` to the image build, not to
the job, so the version is pinned with everything else.

**How to avoid:** Pin the plugin and CLI versions in CI rather than installing
latest, and
treat a beta command as a pilot rather than the backbone of a release runbook.
The capability is genuinely the right one — putting promotion behind a CI job
instead of a human clicking Promote — but the interface is not yet stable.

---

## Gotcha 9: The Edition and Region Floor Is a Hard Stop, Not a Recommendation

**What happens:** A team plans a migration to next-generation DevOps Center and
discovers late that their org cannot enable it.

**When it occurs:** Next-generation DevOps Center requires Professional Edition
with API access or higher and Lightning Experience, and is not available in
Government Cloud Plus or the EU Operating Zone. An org in an excluded region is
not making a choice.

**How to avoid:** Check the edition and region constraints as the first step of
any migration assessment, before the blocker analysis. If the org is excluded,
the managed-package product remains the supported path and the assessment is
over.

---

## Gotcha 10: Bitbucket Support Is Beta and GitHub Is Not

**What happens:** A team standardized on Bitbucket adopts next-generation DevOps
Center on the strength of "Bitbucket is supported" and finds beta-level rough
edges in a production release process.

**When it occurs:** Next-generation DevOps Center documents GitHub and Bitbucket,
with Bitbucket in beta. The managed-package product's Bitbucket support is
likewise documented as beta.

**How to avoid:** Treat a beta source-control provider as a pilot, run it
alongside the existing process for at least a full release cycle, and do not
decommission the old path until the beta has carried a real release. If the
organisation cannot tolerate that, GitHub is the lower-risk choice.

---

## Gotcha 11: Work Items Accumulate Until the List Is Useless

**What happens:** Finding an in-flight work item means filtering past years of
closed ones, and `git branch -r` is equally unusable because the merged branches
were never deleted.

**When it occurs:** By default. Nothing prunes, and the reasonable-sounding
argument that closed work items are the audit trail keeps anyone from deciding
otherwise.

**How to avoid:** Decide a retention window explicitly and write it down. The
durable audit artifacts are the commits and the pull requests, which persist
independently of the work item record; the work item's value after close is
mostly navigational. Delete merged branches on a cadence at the same time.

---

## Gotcha 12: Coding Agents Commit at Machine Speed

**What happens:** An AI coding assistant with repository access produces a volume
of commits that outpaces human review, and something lands in a pipeline branch
that nobody read.

**When it occurs:** Any team that has given an agent write access without a
policy. This is the specific problem next-generation DevOps Center's governance
layer exists to address — it defines policies covering coding agents as well as
users, and the DevOps Center MCP tools are designed to be driven from an
MCP-enabled IDE with a user-facing client.

**How to avoid:** Set the agent policy before granting the access, not after the
first incident. The same rule from Gotcha 2 applies with more force to an agent
than to a human: an agent commits to a work-item branch, and the promotion gate
is where a human looks at it.
