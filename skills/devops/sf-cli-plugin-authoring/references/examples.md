# Examples — sf CLI Plugin Authoring

## Example 1: Internal "guarded deploy" plugin command

**Context:** A platform team wants every CI pipeline that deploys to UAT or prod to first run a custom org-state validation. Today this is duplicated across five pipelines as a 60-line bash preamble. The team wants a single `sf company deploy guarded` command that runs the validation and then delegates to `sf project deploy start`.

**Problem:** A bash wrapper can't return a typed JSON result. Pipelines that today parse the deploy summary will see different stdout shapes from each pipeline copy of the bash, and any change to the validation logic requires updating five repos.

**Solution:**

```ts
// src/commands/company/deploy/guarded.ts
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { Flags, SfCommand } from '@salesforce/sf-plugins-core';
import { Messages } from '@salesforce/core';

const exec = promisify(execFile);

Messages.importMessagesDirectory(__dirname);
const messages = Messages.loadMessages('@company/sf-deploy-tools', 'company.deploy.guarded');

export type GuardedDeployResult = {
  validation: { passed: boolean; findings: string[] };
  deploy: { id: string; success: boolean; numberComponentsDeployed: number };
};

export default class GuardedDeploy extends SfCommand<GuardedDeployResult> {
  public static readonly summary = messages.getMessage('summary');
  public static readonly description = messages.getMessage('description');
  public static readonly examples = messages.getMessages('examples');

  public static readonly flags = {
    'target-org': Flags.requiredOrg(),
    'source-dir': Flags.directory({ char: 'd', exists: true, required: true }),
  };

  public async run(): Promise<GuardedDeployResult> {
    const { flags } = await this.parse(GuardedDeploy);
    const conn = flags['target-org'].getConnection();

    this.log('Running pre-deploy validation...');
    const findings = await runOrgStateValidation(conn);
    if (findings.length > 0) {
      this.error(messages.getMessage('error.validation-failed', [findings.length]), { exit: 1 });
    }

    const username = flags['target-org'].getUsername();
    const { stdout } = await exec('sf', [
      'project', 'deploy', 'start',
      '--json',
      '--target-org', username!,
      '--source-dir', flags['source-dir'],
    ]);
    const deploy = JSON.parse(stdout) as { result: GuardedDeployResult['deploy'] };

    return {
      validation: { passed: true, findings: [] },
      deploy: deploy.result,
    };
  }
}

async function runOrgStateValidation(_conn: unknown): Promise<string[]> {
  // Project-specific checks, e.g., verify no scratch orgs are pending cleanup.
  return [];
}
```

**Why it works:** The typed `GuardedDeployResult` is the public contract — every consumer parses `result.validation.passed` and `result.deploy.success` from the JSON envelope. Validation logic lives in one repo. The `sf project deploy start` shell-out keeps the deploy semantics identical to a stock `sf` invocation, so no deploy-behavior surprises.

---

## Example 2: Migrating an `sfdx` plugin command to `sf` v2

**Context:** A team's existing plugin exposes `sfdx myco:org:diff`. Customers' CI runs invoke this colon-spelling. The team is publishing a v2 release that uses the space-separator style.

**Problem:** Renaming wholesale breaks every consumer. Keeping only the colon style means new customers can't use natural `sf myco org diff` invocation. Both spellings need to coexist for at least one major version.

**Solution:**

```ts
// src/commands/myco/org/diff.ts
import { Flags, SfCommand } from '@salesforce/sf-plugins-core';

export type OrgDiffResult = { differences: number };

export default class MycoOrgDiff extends SfCommand<OrgDiffResult> {
  public static readonly summary = 'Diff metadata between two orgs.';
  public static readonly examples = [
    '<%= config.bin %> <%= command.id %> --source SourceOrg --target TargetOrg',
    'sfdx myco:org:diff --source SourceOrg --target TargetOrg   # deprecated',
  ];

  // Legacy sfdx-style invocation. Held for one major version, then removed.
  public static readonly aliases = ['myco:org:diff'];
  public static readonly deprecateAliases = true;

  public static readonly flags = {
    source: Flags.string({ required: true, summary: 'Source org alias.' }),
    target: Flags.string({ required: true, summary: 'Target org alias.' }),
  };

  public async run(): Promise<OrgDiffResult> {
    const { flags } = await this.parse(MycoOrgDiff);
    const differences = await diffOrgs(flags.source, flags.target);
    return { differences };
  }
}

async function diffOrgs(_a: string, _b: string): Promise<number> { return 0; }
```

In `package.json`, confirm `"oclif": { "topicSeparator": " " }`. With `deprecateAliases: true`, invoking `sf myco:org:diff` (or `sfdx myco:org:diff`) prints a warning naming the new spelling but still runs.

**Why it works:** Old and new spellings resolve to the same command class, so behavior cannot drift. The deprecation warning gives consumers a runtime nudge to migrate without breaking pipelines. After at least one major-version cycle (typically 6+ months), the alias is removed.

---

## Example 3: Plugin that runs without an authenticated org

**Context:** A team wants a plugin command that converts a JSON schema file to a Salesforce custom-metadata-type definition. The command is purely a file transform — no org connection.

**Problem:** Beginners reach for `Flags.requiredOrg()` because every example they see uses it. The result is a command that fails when invoked with `sf myco transform schema --input schema.json` and no `--target-org`, even though the org is irrelevant to the operation.

**Solution:**

```ts
// src/commands/myco/transform/schema.ts
import { readFile, writeFile } from 'node:fs/promises';
import { Flags, SfCommand } from '@salesforce/sf-plugins-core';

export type TransformResult = { outputPath: string; fieldCount: number };

export default class TransformSchema extends SfCommand<TransformResult> {
  public static readonly summary = 'Convert a JSON schema file to a CMDT XML.';

  public static readonly flags = {
    input: Flags.file({ char: 'i', exists: true, required: true }),
    output: Flags.string({ char: 'o', required: true }),
    // Note: no target-org flag. This command is offline.
  };

  public async run(): Promise<TransformResult> {
    const { flags } = await this.parse(TransformSchema);
    const schema = JSON.parse(await readFile(flags.input, 'utf8')) as { fields: unknown[] };
    const xml = renderCmdt(schema);
    await writeFile(flags.output, xml, 'utf8');
    this.log(`Wrote ${flags.output} with ${schema.fields.length} field(s).`);
    return { outputPath: flags.output, fieldCount: schema.fields.length };
  }
}

function renderCmdt(_s: unknown): string { return '<CustomMetadata/>'; }
```

**Why it works:** Omitting the org flag matches the command's actual contract. Users invoking `sf myco transform schema --input … --output …` with no auth context succeed. The `--json` shape still works (no special handling needed for offline commands).

---

## Anti-Pattern: Hand-parsing `process.argv` instead of using flag factories

**What practitioners do:** Inside `run()`, call `process.argv.slice(2)` and parse manually because "the flag factory doesn't support exactly what I need."

**What goes wrong:**

1. The `--json` flag wrapper is bypassed; calling `console.log(JSON.stringify(...))` directly produces malformed output (missing the `status` envelope, missing the `result` key).
2. The plugin's `--help` output omits the manually-parsed flags, so users discover them only by reading source code.
3. `--flags-dir` (which lets users supply flags as files in a directory) doesn't work; flag-driven CI patterns break.

**Correct approach:** If the flag factories don't model your shape, compose two simpler flags or use `Flags.custom<T>({ parse: async (raw) => { ... } })` to extend the system. Hand-parsing argv is almost never the right answer.
