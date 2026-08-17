# Licensing

SfSkills is **source-available**, not open source. The code is public and you can
read all of it. Whether you may *use* it for free depends on the size of the
organisation you're using it for.

The governing document is [`LICENSE`](./LICENSE) — the
[PolyForm Small Business License 1.0.0](https://polyformproject.org/licenses/small-business/1.0.0),
SPDX identifier `PolyForm-Small-Business-1.0.0`. This page is a plain-English
guide to it, and the license itself wins wherever the two disagree.

## Free, no permission needed

You can use, modify, and redistribute SfSkills at no cost if your company has:

- **fewer than 100 people** working for it as employees and independent
  contractors, **and**
- **less than USD 1,000,000 in total revenue** in the prior tax year
  (the license adjusts that 2019 figure for inflation via the US BLS CPI-U).

That covers, for example:

- individual developers, admins, and architects
- freelancers and independent consultants, including on billable client work
- small and mid-sized consultancies and SIs under both thresholds
- startups and small ISVs
- students, trainers, and researchers

Note that "your company" is defined broadly. It sweeps in parents, subsidiaries,
and any organisation under common control — so a small team inside a large
enterprise does not qualify on the strength of the team's own headcount.

## Requires a commercial license

If your organisation is over either threshold, you need a license from me before
using SfSkills for its benefit. That includes internal use — running it on your
own developers' machines against your own org still counts.

Typically this means:

- enterprises and their in-house Salesforce teams
- consultancies, SIs, and partners above 100 people or USD 1M revenue
- ISVs embedding any part of SfSkills in a product or service
- managed-service providers running it on behalf of clients

**To get one, email <pranav.nagrecha11@gmail.com>** with your organisation's
name, roughly how many people would use it, and what you're planning to do with
it. I'll send back terms.

There's no pricing page yet — early commercial terms are negotiated directly,
and I'd rather hear your use case than have you bounce off a number.

## Questions this usually raises

**Is this open source?** No. It fails the OSI definition because the grant of
use is conditional on company size. SPDX records it as neither OSI-approved nor
FSF-libre. If an OSI-approved license is a hard requirement for you, this
project won't satisfy it.

**Can I still read, fork, and patch it?** Yes. The source stays public, forking
and modification are permitted, and the patent grant applies. The size condition
governs *use*, not visibility.

**What about versions released before this change?** Earlier releases were
distributed under permissive terms — the repository under Apache-2.0, and
`sfskills-mcp` 0.4.6 and 0.4.7 on PyPI declaring MIT. Those grants were made and
cannot be withdrawn: if you obtained a copy under them, you keep those rights to
that copy for good. This license governs releases made from 2026-08-15 onward.

**What if we're right at the threshold?** Ask. I would rather answer than have
you guess, and the answer costs you nothing.

**We're a nonprofit / government body / school.** There's no automatic carve-out
in the license text, but get in touch — these are exactly the cases worth
discussing.

**Do I need a license to contribute?** No. Contributions are welcome under
[`CONTRIBUTING.md`](./CONTRIBUTING.md). By opening a pull request you agree that
your contribution is licensed to the project under these same terms.

## Attribution

The license requires that anyone you pass a copy to also receives these terms
(or the URL) plus the `Required Notice:` line carried in [`LICENSE`](./LICENSE):

> Required Notice: Copyright 2026 Pranav Nagrecha (https://github.com/PranavNagrecha/AwesomeSalesforceSkills)

Keep that line intact in any redistribution.
