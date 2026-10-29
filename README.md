# coduo-skills

The skills Coduo uses to build products with coding agents: turn an idea into a GitHub epic, cut the
epic into tickets, run the tickets unattended with [coduo-afk](https://github.com/sahildave/coduo-afk),
and land the result. Also product memory, prototypes, landing copy, pricing and SEO research.

This repo is a Claude Code plugin marketplace with two plugins:

| Plugin | What it is |
|---|---|
| `coduo` | The 26 skills below, hosted here |
| `mattpocock-skills` | [Matt Pocock's engineering skills](https://github.com/mattpocock/skills), installed from upstream. `coduo-epic`, `coduo-tickets` and `coduo-implement` wrap his `to-spec`, `to-tickets` and `implement`, and the coduo-afk closeout review runs his `code-review` |

## Install

```bash
claude plugin marketplace add sahildave/coduo-skills
```
```bash
claude plugin install coduo@coduo-skills
```
```bash
claude plugin install mattpocock-skills@coduo-skills
```

To turn them on for one project only, commit this to the project's `.claude/settings.json` instead:

```json
{
  "extraKnownMarketplaces": {
    "coduo-skills": { "source": { "source": "github", "repo": "sahildave/coduo-skills" } }
  },
  "enabledPlugins": {
    "coduo@coduo-skills": true,
    "mattpocock-skills@coduo-skills": true
  }
}
```

## The workflow

| Step | Skill | Output |
|---|---|---|
| Think it through | `coduo-discuss` | `docs/product/<idea>/discussion.md` |
| Write the epic | `coduo-epic` | One GitHub issue with the spec and an `afk:` block |
| Cut the tickets | `coduo-tickets` | Child issues, a dependency DAG on the epic, the `tasks:` block |
| Run it unattended | `coduo-afk` | A branch, one verified commit per ticket, a PR |
| Park and resume | `coduo-afk-park` | A resume note on each epic's PR |
| Land it | `coduo-land-pr` | Merged PR, closed issues, no leftover branches or worktrees |

## All skills

**Building**

- `coduo-implement` — implement a spec or tickets with fidelity checks: experience criteria first, every stub finished or ticketed, verification shown, not described.
- `coduo-tasks` — write a `tasks/` folder for an overnight run with no tracker and no PRs.
- `coduo-housekeeping` — close shipped-but-open tickets, file untracked work, and route what is left to an agent or a person.
- `coduo-debate` — settle a plan or diagnosis by debating it with an independent sub-agent until you agree.
- `karpathy-guidelines` — baseline coding discipline: surgical changes, minimal solutions, stated assumptions, verifiable steps. Adapted from [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills).
- `setup-coduo-toolchain` — install lint, format and type checks on the base branch so unattended lanes inherit them.
- `beautiful-dag` — draw a phased Mermaid dependency graph for a plan or an epic.

**Design and verification**

- `coduo-product-prototype` — build the frontend prototype an unattended run later wires a backend behind.
- `coduo-design-export` — export Paper artboards into the repo as the binding spec.
- `coduo-design-update` — treat a UI branch's design as final and bring tests, baselines and docs into line.
- `coduo-code-flow` — build an interactive architecture and flow map for a repo.
- `coduo-flow` — turn a session into linked topic notes and a rendered flow map.
- `coduo-install-on-phone` — build and install the app on real test phones, then say what to test.
- `coduo-mac-drag` — drive a real cross-app drag and drop on macOS to test a drop target.

**Product and go-to-market**

- `coduo-product-market` — keep a repo's positioning signals, business rules and feature list.
- `coduo-pricing` — report the decided price, or price the competitors into a first range.
- `coduo-landing-copy` — grade a landing page section by section and suggest copy.
- `coduo-seo-pain-point` — collect competitor complaints for pain-point SEO.
- `coduo-seo-ai-answers` — check how AI assistants answer a category's buyer questions.
- `coduo-jev` — design a TypeSafe Jev integration for one decision (slash-only).

## Contributing

These skills are edited in the maintainer's local skill store and copied here with
`scripts/sync-from-store.sh`, which refuses to publish a personal name or path. Open an issue for a
bug or a proposal. A pull request to a skill file is welcome, and the maintainer ports it to the store.

## License

MIT. `mattpocock-skills` is Matt Pocock's, under its own MIT license.
