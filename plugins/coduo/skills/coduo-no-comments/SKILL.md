---
name: coduo-no-comments
description: "Prune the comments a change adds: delete narration and restated code, and move every comment that states a policy or a surprise in our code into code that says it. Runs as a build step of coduo-implement, on the task's own diff. Use for /coduo-no-comments, 'prune comments', or 'find useless comments in this repo'."
disable-model-invocation: false
---

A comment that restates the code costs reading and goes stale. A comment
that carries a fact means the code should carry it. So delete the first kind
and move the second kind into code.

## Scope

The comment lines your change adds: `git diff <base>` (base is the branch you
started from) plus every new untracked file from `git status --short`.
Comments on lines you only moved are older comments and out of scope, as are
comments outside source code (config, docs, fixtures).

A whole repo or directory is in scope only when the user names it. There,
report the verdicts and delete nothing until the user says.

## Keep only these

1. Legal or license headers.
2. Behaviour forced by something we cannot change: a dependency, platform,
   vendor or protocol. It must be true today on a live path; check it.
3. A lint suppression whose rule is wrong, pedantic or style-only. A
   suppression of a rule that catches real bugs is a RESHAPE: fix the code,
   then delete it.
4. A doc comment on an exported function or type that states its contract.
5. An issue or RFC link that explains a constraint the code cannot express.
6. A comment a tool reads: a directive, pragma, shebang or magic comment.

Everything else goes: narration, restated code, history, measurements,
commented-out code, "IMPORTANT" and "do not remove" without a proven keep.
When unsure, ask whether a reader of the code alone would lose a fact. If
not, it dies. If so, it is a RESHAPE, never a KILL.

## Steps

1. **List the verdicts:** KILL, KEEP (with the keep number and the proof), or
   RESHAPE. A RESHAPE is a comment that explains a surprise in our code or
   states a policy the code does not show (a cache TTL, a fail direction, an
   ordering or retention rule).
   Do this yourself in an AFK lane; you may not spawn. Interactive, on a
   large diff, you may give it to a `reader` sub-agent on Sonnet with
   `git diff <base> -U12` and this file, report only. Then recheck its KILLs
   on doc comments and on comments that name a dependency or platform; it
   gets those wrong.
2. **Delete the KILLs.** Comment lines only.
3. **Do each RESHAPE** with the smallest thing that works: a name, a named
   constant (`MERGED_TTL_MS`), an extracted function, a type, or a test that
   pins the policy. Then delete the comment. A workaround is removed, not
   renamed. If the reshape needs code your diff does not already touch,
   leave the comment and report it open; this should be rare. Never delete a
   policy comment without its reshape: the code then says less than before.
   Do not shorten a comment to save it.
4. **Run the checks once, after the edits.** Under `coduo-implement` that is
   its own Verify run, not an extra one.
5. **Report** the deletion count, the reshapes done, the keeps with their
   proof, and the reshapes left open.

## Examples

- `// loop over the lanes` → KILL.
- `// merged PRs are cached 10 min; on error treat as not merged` → RESHAPE:
  `MERGED_TTL_MS`, and a test for the error path.
- `// spawnSync blocks the event loop, so an in-process server cannot answer`
  → KEEP 2.

Adapted from pstack's `no-comments` and its Comment Sicko agent
(cursor/plugins, MIT, Lauren Tan).
