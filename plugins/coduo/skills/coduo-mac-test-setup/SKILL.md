---
name: coduo-mac-test-setup
description: Generate, for the current repo, an owner-run wizard that sets up a Mac app's staging test environment, then hand the owner one command. Covers copying the release read vars from prod to dev in the secret store, a staging-only test sign-in switch and random password, the two fixture users (free and pro) in the dev auth project, and a probe that staging answers and production 404s. Use when asked to set up staging test accounts, the test sign-in, or Mac-app testing for a product.
disable-model-invocation: false
---

# Mac app test setup, as an owner wizard

A human runs this because the steps need a person at a dashboard.

## Steps

1. **Read the repo's bindings.** Done when you can fill every variable in the config block of [stages-example.sh](stages-example.sh) from the repo, not from guesses: the secret store project and path (use the repo's wrapper if it has one), the dev auth project ref and the prod one, staging and production URLs, the fixture emails, the test sign-in route, its two env var names, the release var names, and the repo's staging-only grant command. A value you cannot find stays a `<placeholder>`; the wizard refuses to run on it, so ask the owner. Background: the repo's test-identity decision doc; releases are `coduo-release-mac-app` (it owns the read-token vars, do not repeat it).
2. **Generate the wizard.** Follow the `wizard` skill: copy [stages-example.sh](stages-example.sh) to the repo's `scripts/` (or a scratch path); the library above the `STAGES` marker stays byte-identical to `wizard/template.sh`. Change only the config block. If the repo has an Infisical wrapper, replace `inf_get` and `inf_put` and keep their contract: a value only in a pipe, never in an argument.
3. **Verify, do not run.** `bash -n`, `shellcheck`, `chmod +x`. Run only `<wizard> --check`: it validates the config, then exits with no network call and no write. Run it once as generated, and once on a scratch copy with a production-looking value to show it fire. Without `--check` the wizard opens browsers and blocks on a human, and it stops at once if stdin is not a terminal.
4. **Hand over.** Give the owner one line: `cd <abs repo path> && <wizard path>`. Stage 4 prints the one command to hand back to you (the repo's staging-only grant, which makes the pro user Pro).

## The five stages

| # | Does | Writes |
|---|---|---|
| 1 | Copies the release read token and repo name, prod to dev | Secret store dev |
| 2 | Sets the test sign-in switch to `true` and a random password (`openssl rand -base64 32`) | Secret store dev |
| 3 | Password to the clipboard, opens the dev auth Users page, owner creates free and pro with auto-confirm, clipboard cleared | Nothing |
| 4 | Owner pastes the pro user's id (public); wizard prints the grant command | Nothing |
| 5 | Probes staging for both fixtures (expects a redirect) and production (expects 404) | Nothing |

## Rules the wizard keeps

- **Refuses before stage 1** if any variable is empty or a `<placeholder>`, the destination env is not `dev`, `development`, `staging`, `test` or `qa`, the auth ref equals the prod ref or looks like prod, or the staging URL equals production or lacks a staging label.
- Vars go to the secret store only, never `.env` or a CI secret. Secrets pass only through pipes, unexported shell variables held briefly while the wizard runs, one 0600 temp file and, in stage 3, the clipboard; none reaches an argument, a log or the history. The temp file is emptied after each write and removed on exit, including Ctrl-C, but a SIGKILL or power loss during a write can leave a secret in it.
- Every overwrite asks first, so re-running is safe.
- Staging needs a redeploy to see new values; stage 5 asks for it before probing.
- The test sign-in route must itself fail closed (404 unless the switch, a preview environment, the dev auth project and the server-side password all hold). The caller sends no password, so anyone who reaches staging can sign in as a fixture. So never enable the switch in production, accept only a fixed allowlist of fixtures, and restrict who can reach staging. If the repo has no such route, stop: that is a separate ticket, not this wizard's job.
