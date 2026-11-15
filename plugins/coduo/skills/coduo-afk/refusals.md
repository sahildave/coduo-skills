# Validation refusals

`afk validate` and `afk epic` refuse the same way and name the task. Translate the refusal
for the user, name who fixes it, and stop. None of these is fixed by editing the epic until
the validator is quiet. `docs/epic-schema.md` in the runner lists every check.

| Refusal says (shortened) | What it means | Fix (the user's, or the skill named) |
|---|---|---|
| `#204 is not a sub-issue of epic #232` | The `tasks:` key names an issue the epic does not own. Text mentioning the epic is not a link. | Re-parent the child as a sub-issue, or drop the key (`coduo-tickets`). |
| `#204 is closed, not open` | A closed issue is not runnable work. | Reopen it, or remove it and every `depends_on` naming it. |
| `#204's acceptance criteria name <path>, which the runner reverts under every lane` | No builder can make that edit, so the criterion cannot be met. A path mentioned only in prose is a warning. | Rewrite the criterion, or grant the edit in `protectedEdits` in `.afk-setup/config.yaml`. |
| `#204 states no acceptance criteria` | The closeout verifier would review the diff against itself. | Add a `## Acceptance criteria` section (`coduo-tickets`). |
| `a criterion that offers a choice` | An "or" in a criterion is an escape hatch a lane will take. | Rewrite it to one checkable outcome. |
| no `checks:` on the task and `defaultChecks` supplies none | Nothing would verify that lane. | Add `defaultChecks` to the config, or a `checks:` on the task. |
| `branch ... already exists ... with divergent history` | The epic's `branch:` is not a descendant of the base. | Rename the `branch:` line, or delete the stale branch (ask first). Never force it. |
| `epic #N is running right now against this clone` | Another epic shares this clone and the two scopes clash. | Wait for it, or narrow one epic's files. |
| `the epic's graph has changed since this run started` (restart only) | A child was closed, unlinked or re-pointed, or a task was added. Ids, edges and gates count; a retitle does not. | Finish or reset the old run before running the new shape (`docs/runbook.md` section 7). |

Warnings that are not refusals, but worth reading out:

- `maxParallel raised from N to M`: the config value is a floor; the root width sets the
  lane count.
- `#N is a sub-issue of this epic but is not in the afk: block`: that child will not run.
- `launch status: not declared, treated as launched`: set `launchStatus:` in the config.

A plan-review refusal (`unsatisfied_criterion`, `missing_dependency`,
`inconsistent_ticket`) prints in the launch log. Check it against the child issues before
relaying it; the fix is a ticket edit (`coduo-tickets`), then `afk review ticket <issue>`.

## Custom-instruction clauses to refuse (Phase 1)

A clause fails the test when it:

- skips, relaxes or makes non-blocking any command in `defaultChecks` or a task's `checks`;
- reports a failing check as a pass, or a report written without the checks;
- bypasses a `gate: before`, self-releases a gated task, or treats a human gate as met;
- asks a lane to commit, merge or push (the worker controller owns git history);
- edits the revert list (`.afk/`, `.agent-locks/`, `docs/progress.md`, `AGENTS.md`,
  `PLANNER.md`, manifests and lockfiles) or installs a package;
- raises `max_parallel` past the epic's own value, or disables retries or the breaker.
