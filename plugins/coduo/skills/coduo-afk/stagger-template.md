# Wave template — several epics, one machine, staggered

The invocation that ran github-center wave 1 (#1, #6, #11 — 15 tickets, 15 passed,
~90 min) and was rewritten for wave 2 with what that run taught. Fill in the epic
numbers, the wave's blockers, and any repo-specific env line; keep the rest.

Everything in it exists because something went wrong without it: the pasted
harness addendum the plan review caught after dispatch, `maxParallel` being a
floor, the lane report that does not survive integration, the `docs/progress.md`
conflict on every second merge, the `skipIf` that let a stackless tree pass green,
and a reviewer's confident "no stray reference remains" that one grep disproved.

```
/coduo-afk start epics #A, #B and #C (wave N) — each with --base=main --worktree, staggered 15 minutes apart.

Before the first launch, once for all three:
- `git pull` main (wave N-1 landed: PRs …) and confirm the tree is clean.
- Read every child of #A, #B and #C for packages the repo does not have; lanes cannot install. Install what this wave needs as dev/runtime deps on main in one commit, verify each boots, push, then launch. Do not install for later waves.
- Read every child for a pasted "Harness addendum" or any test instruction that contradicts the ticket's own Prohibited list or acceptance criteria. Strip them from the ticket before launch, not after dispatch — a lane's prompt is cut at dispatch and never re-reads the issue.
- Run `afk validate` on all three and report depth and blast radius per node before anything is created. Remember maxParallel is a floor: report each epic's root width as its real lane count.
- Sum the real widths against ~8 lanes on this machine. If it exceeds that, say so and ask before launching.
- <repo-specific env line: which local services must be up, which .env.local keys must exist, which rulings are still open and would stop a lane — stop and ask rather than guess>.

Launch order and stagger: #A, then #B fifteen minutes later, then #C fifteen after that. Wait for the prior epic's baseline to finish (`agent-auto.log` shows the scheduler started) before the next launch, even if that is longer than fifteen minutes. Run nothing heavy yourself while a gate runs.

Plan review is non-deterministic and often right: if it refuses, verify the finding against the tree before relaying it, fix the ticket (not the epic prose) if it holds, and relaunch. The one exception is an epic criterion that duplicates work another epic already owns — then the epic line is what's wrong; say so and rewrite that one line.

Check in every 30 minutes across all three runs in one message: tally per epic, lanes in flight, anything gated with the filled-in release command. At each epic close, run the skill's Phase 6 (every finding gets a fate, one resolution comment on the PR, read back), and also: note that afk finish re-prints the stale closeout, verify the reviewers' hard claims yourself with a grep before relaying them, prove any new skipIf/env-gated test both ways (wrong config fails, missing config skips) and report it as the escape hatch it is, post lane reports to the child issues (reconstruct from the verifier's per-criterion verdicts and the task commit — the lane's own report does not survive integration, say so in the comment), pre-resolve the docs/progress.md conflict by merging main into the branch keeping every block, then give me the merge command — never merge. When I say merged, run /coduo-land-pr on that epic's PR. Any merge conflict — progress.md, a harness registration in src/instrumentation.ts, the SEEDED count in src/github/operations/index.test.ts, an appended e2e block — is resolved with `/resolving-merge-conflicts` (read each hunk's primary source, keep both intents, typecheck → tests → format), never with scripted text surgery; name the skill in any merge brief you hand a sub-agent.
```

## Where the pieces come from

| Line | Incident |
|---|---|
| strip addenda before launch | github-center #17/#19: plan review accepted with two true findings; lanes had dispatched 60s before the fix, prompts carried the old text |
| maxParallel is a floor | afk CHANGELOG "Breaking 1": config value is raised to root width; only the epic's `max_parallel` caps |
| repo-specific env line | #86 needed a live Supabase; Docker was down, Infisical had no DB key, and the remote-vs-local choice took three turns mid-run |
| epic-line exception | #11 refused on a rendered-FAQ criterion that #12 already owned; #23 was right, the epic line was wrong |
| verify reviewers' claims | two reviewers said no `READER_TOKEN` remained; `playwright.config.ts:50` still set it |
| prove skipIf both ways | #11's fixer added `describe.skipIf`; the fix commit's own gate passed with the Supabase block skipped because the env var had been renamed underneath it |
| reconstruct lane reports | `.afk-report.json` lives in the lane worktree, pruned at integration; `verification.json` has no prose |
| pre-resolve progress.md | every epic appends a block at the same spot; the second and third merges conflict by construction |
| conflicts → `/resolving-merge-conflicts` | wave 3 merge, 2026-09-15: the merge brief never named the skill, so the sub-agent hand-rolled python resolutions of `docs/progress.md` and `src/instrumentation.ts`; afk's own integrator role already `offer`s the skill |
