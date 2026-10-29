---
name: coduo-land-pr
description: |
  Land a pull request and leave nothing behind: merge it when told to and CI is
  green, close every issue it shipped with a pointer to the merge, remove its
  worktree, delete its branch locally and on the remote, and put the checkout
  back on a fresh base. Runs /code-review first when the PR has no review at
  its head commit. Use for "merged", "merge it and clean up", "close the
  issues and clean up", "land #156", when a coduo-afk run's PR is merged, and
  for a sweep of stale branches, worktrees and orphaned build output ("clean up
  branches", "what needs a PR", "clean up the targets").
disable-model-invocation: false
---

# Coduo land PR

For the user, landing is one word: they say "merged" or "merge it", and when you
finish, the PR's issues are closed, its branch and worktree are gone, and the
checkout sits on an up-to-date base. They should never have to ask for the
pieces one at a time.

**This PR only.** Other agents and AFK runs share this machine and often this
clone. Touch this PR's branch, this PR's worktree, and the issues this PR
shipped. Anything else you notice goes in the report, not in a delete.

Several PRs in one request ("merge all 3"): run the steps once per PR, in
order, and write one report.

## Step 1 — Identify

```bash
gh pr view <n> --json number,url,state,baseRefName,headRefName,mergeCommit,mergeStateStatus,closingIssuesReferences
```

With no number, take the PR for the current branch (`gh pr view`), or the one
the conversation was just about.

**Done when** you know the PR, its base, its head branch and whether it is
merged.

## Step 1b — Review, if nobody has

Skip when the PR is already `MERGED`. Otherwise read the head SHA
(`gh pr view <n> --json headRefOid`) and look for this skill's marker in the
PR comments:

```bash
gh pr view <n> --json comments -q '.comments[].body' | grep -o 'coduo-land-pr:reviewed [0-9a-f]*'
```

- A marker naming the current head SHA: reviewed, go to Step 2.
- No marker, or a marker naming an older SHA (commits landed after the
  review — the newest commit is the least reviewed): start a fresh sub-agent
  that runs `/code-review` against the PR's base branch, with the PR number,
  head SHA and linked issues in its brief. `code-review` is vendored and
  posts nothing; this skill posts its report as a PR comment ending in
  `<!-- coduo-land-pr:reviewed <head-sha> -->`.
- The review names a blocker (a Spec miss or a Standards violation it marks
  must-fix): stop before Step 2, list the blockers, and wait. Nits go in the
  comment and do not stop the merge. One review per head SHA: after a fix
  pass, review only the new commits, and merge on that — do not loop.

**Done when** the head SHA carries a marker and no blocker is open.

## Step 2 — Merge, only when told

- Already `MERGED`: skip to Step 3.
- The user said "merge" in this request: `gh pr checks <n>` must be all green
  (run `gh pr checks <n> --watch` in the background if they are still going).
  Then merge with the method the repo uses (`gh pr list --state merged -L 5`
  shows it; `gh repo view --json squashMergeAllowed,mergeCommitAllowed` shows
  what is allowed). Leave out `--delete-branch`: it switches branches in
  whichever checkout you run it from, and Step 4 does the teardown in the right
  order.
- A red check or a conflict: stop and name the failing check or the conflicted
  files. Resolve conflicts with `/resolving-merge-conflicts`, and only when the
  user asked for the merge.
- Not merged, and the user only said "clean up": stop. Say that the PR is
  open and that you'll land it once they say merge. "Clean up" never means
  merge.

An AFK epic's PR is merged by a human (the runner never lands its own work),
so "merge it" from the user is the authorization, and it covers this PR only.

**Done when** the PR's state is `MERGED` and you have the merge commit's SHA.

## Step 3 — Close what shipped

Collect the issues this PR shipped:
- `closingIssuesReferences`
- for an AFK epic PR, the epic and its sub-issues
  (`gh api repos/{owner}/{repo}/issues/<epic>/sub_issues --jq '.[].number'`)
- anything the user named

GitHub closes the referenced issues automatically only when the PR merges into
the default branch, so check each one's state after the merge. Close the ones
still open:

```bash
gh issue close <i> --comment "Shipped in #<pr> (<short sha>)."
```

Close an issue only if the PR actually delivers it. A child whose lane failed
or stayed gated, or a criterion the closeout marked unmet, stays open with a
one-line comment saying what is left.

This step files nothing new. Follow-ups were ticketed at closeout under
`coduo-implement` rule 5 (stubs, and product work too big for the PR). List
them in the report and leave it there.

**Done when** each collected issue is either closed with a merge pointer or
still open with a comment saying why.

## Step 4 — Tear down

Do it in this order: worktree, then prune, then branch. `git branch -d` fails,
silently if stderr is hidden, while any worktree still has the branch checked
out.

```bash
git fetch --prune origin
git worktree list --porcelain          # find the worktree whose branch is <head>
git -C <worktree> status --porcelain   # anything here → stop and show it
git worktree remove <worktree> && git worktree prune
git branch -d <head>
git push origin --delete <head>        # skip if the remote branch is already gone
```

- **Dirty worktree:** stop and show the changes. Never `--force` over them.
  They may belong to a live agent.
- **Squash merge:** `-d` refuses because the branch's commits are not ancestors
  of the base. Check that `git diff origin/<base>...<head> --stat` is empty,
  then use `-D`.
- **The parent folder goes with the worktree.** A worktree usually sits one
  level down, `<parent>/<repo>`, and a project that builds just outside its
  checkout (`target-dir = "../.atlas-target"`) fills `<parent>` with 3–20 GB of
  build output that `git worktree remove` never touches. Once the worktree is
  gone, `ls -A <parent>`. Every remaining entry a build cache (a directory
  holding `CACHEDIR.TAG`, which cargo writes into every target dir) →
  `du -sh` it, `rm -rf <parent>`, and put the size in the report. Any other
  entry → leave `<parent>` and name what is in it.
- **AFK epic runs** keep their worktree at `~/.afk-claude/epics/<slug>-<id>/<repo>`,
  so `<slug>-<id>` is that parent. Check whether `afk finish` already removed
  it; when it is still there, remove the worktree and the parent here.
- **A symlinked `node_modules`** can make `git worktree remove` complain even
  though the tree is clean. Look at `status --porcelain` rather than the
  complaint.
- **The main checkout:** if it has the merged branch checked out, or is on the
  base branch and clean, run `git switch <base> && git pull --ff-only`. If it
  is on some other branch or has changes, it is someone's live work. Leave it
  and say so.

**Done when** neither `git worktree list` nor `git branch -a` shows `<head>`,
its parent folder is gone or named in the report with its contents,
and the main checkout is on `<base>` at `origin/<base>`, or you left it alone
and gave the reason.

## Step 5 — Report

Four lines per PR:
- **Review:** link to the review comment, or "already reviewed at <sha>".
- **Merged:** PR link, merge method, short SHA (or "already merged").
- **Issues:** closed, as links; still open, each with its reason; follow-ups
  already filed.
- **Removed:** worktree path, local branch, remote branch, plus anything you
  left alone and why.

## Sweep: stale branches and worktrees

When the user asks for a cleanup and names no PR ("clean up branches", "what
needs a PR", "delete stale branches"), the audit is what you deliver. Deleting
comes second, after they approve it.

```bash
git fetch --all --prune
git branch -vv
git branch -r
gh pr list --state all --limit 30
git worktree list
```

Put each branch into one class and show the evidence:
- **Merged-dead:** `git merge-base --is-ancestor <branch> origin/<base>`
  succeeds, or it was squash-merged and its diff against the base is empty.
- **Ahead, needs a PR:** has commits ahead of the base and no open PR. Propose
  the PR.
- **Live:** an open PR, a worktree with changes, a branch an AFK run or another
  agent is using, or one the user named as WIP. Leave these alone and carry the
  reason into the summary.

Then find **orphaned build output**: a build cache whose worktree is gone,
left by runs that predate the parent-folder rule in Step 4.

```bash
find ~/.afk-claude/epics "$(dirname "$(git rev-parse --show-toplevel)")" \
  -maxdepth 5 -name CACHEDIR.TAG 2>/dev/null | while read -r tag; do
  cache=$(dirname "$tag"); parent=$(dirname "$cache")
  git -C "$parent" rev-parse --is-inside-work-tree >/dev/null 2>&1 && continue
  find "$parent" -mindepth 2 -maxdepth 2 -name .git | grep -q . && continue
  du -sh "$parent"
done
```

A hit is **live** when its parent sits inside a checkout (a repo's own
`target/`, `.pytest_cache`) or holds one beside it (the main checkout's
`../.atlas-target`). The loop skips both and prints each **orphan**'s parent
with its size; show them as their own table after the branches.

Show the tables and wait. Once approved, run Step 4 for each merged-dead branch,
and `rm -rf` each orphan's parent folder.
Then check that the branches still standing are exactly the keep list and that
`git log --oneline origin/<base> -5` still shows the merges. Report what was
deleted, what was kept and why, and which PRs you propose.
