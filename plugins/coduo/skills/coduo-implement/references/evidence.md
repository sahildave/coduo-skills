# Evidence for a PR body

Pick the evidence class before you capture, keep it the same before and after
the fix, and name it in the report so the reviewer knows why other artifacts
are absent.

| Class | What to capture |
|---|---|
| `static-visual` | One failing-state screenshot and one fixed-state. Not one per navigation step. |
| `temporal` | A recording for an animation, gesture or crash sequence. Add a still only when the final frame matters. |
| `structural-runtime` | The exact log, assertion or red-first test. No media. |

A diff that changes what a route or screen renders is `static-visual` at
least: one capture on the base, one on the branch, for each changed route.
`structural-runtime` is for changes nothing draws.

## Where the files go

Save images to `.agents/evidence/<task-or-issue>/`, numbered by step
(`03-after-save-crash.png`). Keep the folder tracked while the work is open.
The closeout removes it after merge.

In an AFK lane you stop here: the runner commits, and the PR body is not
yours to write. Name the files in your report.

## The PR table

Interactive only. Commit the screenshots, push, and take the sha of the
commit that added them (`git rev-parse HEAD`, again after any amend or later
evidence commit). Then:

```markdown
| Before (`main`, `<sha>`) | After (this branch, `<sha>`) |
| :---: | :---: |
| <img src="https://github.com/<owner>/<repo>/blob/<sha>/.agents/evidence/<id>/<before>.png?raw=true" width="380" alt="failing state"> | <img src="https://github.com/<owner>/<repo>/blob/<sha>/.agents/evidence/<id>/<after>.png?raw=true" width="380" alt="fixed state"> |
```

- Use the sha, not the branch name. A branch URL 404s once the branch is
  deleted; a sha URL keeps working after the folder is removed.
- Use the `blob/<sha>/…?raw=true` form, not `raw.githubusercontent.com`. On
  a private repo the raw host gets no viewer session and the image renders
  blank.
- Use an `<img>` tag. A bare image URL renders as a link.

Check each file landed:

```bash
gh api "repos/<owner>/<repo>/contents/<path>?ref=<sha>" -q .size
```

Anonymous `curl` 404s on a private repo, so it proves nothing there.
