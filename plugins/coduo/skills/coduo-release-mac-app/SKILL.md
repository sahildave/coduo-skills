---
name: coduo-release-mac-app
description: "Release a Mac app that is sold from its own site: bump the version, build, sign, notarize, publish to a private GitHub Release and verify the update feed, from one local command. Use when asked to cut, ship or retry a Mac release, to set up a repo's release script, to fix a failed notarization or a missing update, or to give a site's download route and update feed their release-read token."
disable-model-invocation: false
---

# Release a Mac app, fast and repeatable

A release is cut **locally**, by one script, from a pushed commit. A private GitHub Release is the artifact store; the product's site serves the download and the update feed from it with a read-only token. No CI release workflow: a macOS runner costs more than the Mac in front of you, and the signing identity already lives in its keychain.

Read the project's release script and `AGENTS.md` first; they bind every `<name>` below. Everything project-specific (repo, tag format, signing identity name, notary profile, secret names) sits in that script's header or in one small `release.env.example`. Never hard-code a team id, token or path into this skill's output.

## Steps

1. **Preflight, on a clean pushed tree.** Done when all hold: `git status` is empty, HEAD is on `origin/<branch>`, every version-carrying file shows the same version, and the tag, if it exists, points at HEAD. A script that cannot say these four things is the first thing to fix.
2. **Secrets from the secret store, names only.** Pin the production environment in the script (`INFISICAL_ENV=prod` or the project's equivalent); a build that falls back to a dev environment ships dev keys and nothing says so. Read the signing-key pin, the analytics key and the update-signing key from the store at build time. Print names and short hashes, never values. Done when the script prints which environment it pinned.
3. **Bump the version.** One command edits every version file together (the project's `release:prepare` or equivalent), commits, and pushes. The tag must equal the version files; a mismatch makes the updater offer one version and install another.
4. **Build and sign.** Archive Release for the Developer ID identity, pinned by SHA-1 from the secret store and matched against the keychain, never the keychain's own first hit. Done when `codesign -dvv` on the exported app shows the Developer ID authority and a secure `Timestamp=`.
5. **Notarize and staple the DMG.** `notarytool submit --wait --output-format json`, then read the JSON `status`; the exit code lies. Anything but `Accepted` is fatal. Then `stapler staple` and `stapler validate` the DMG (the bundler only staples the app).
6. **Update signature after stapling.** Sign the stapled DMG (Sparkle's `generate_appcast` / `sign_update`, or the Tauri minisign `.sig`). Stapling changes the bytes, so an earlier signature never verifies. Use the product's own key account, never the default one.
7. **Assert the artifact, not the build.** `spctl -a -vvv -t install` must say `Notarized Developer ID`; the update-signing public key in the app must not be empty or a placeholder; no debug-only package or asset may ship (grep symbols and `Assets.car`). Done when every check prints its result.
8. **Publish as a draft.** Name assets exactly as the site's download route and feed look them up (a name carrying version and arch, e.g. `<App>_<version>_universal.dmg` plus its `.sig`). `gh release create --draft`; on retry `gh release upload --clobber`, and refuse when the release is already published, since a clobber swaps bytes under installed apps.
9. **Verify the draft, then publish.** Download the DMG on a Mac that never saw the app and open it: Gatekeeper's verdict on a quarantined copy is the one that counts. Confirm the DMG and `.sig` are attached, then `gh release edit <tag> --draft=false`.
10. **Verify the published feed.** From the site, the download route answers a 302 to a `.dmg`, and the update feed called with an older version returns the new one with its signature (`curl -sS -o /dev/null -w '%{http_code} %{redirect_url}'`, print the status and file name, never the signed query). Done when both answer and a build one version behind sees the update.

## The site's read token

The download route and feed read the private repo's Releases with `<APP>_RELEASE_READ_TOKEN` (a fine-grained token, `contents: read` on that one repo, nothing else) and `<APP>_RELEASE_REPOSITORY` (`owner/repo`). Both live in the secret store and reach the Worker or site through the deploy's env compose step, never a provider dashboard. A preview or staging deploy may hold the same read-only value as production. Missing, the route answers 503 (or 500) naming the missing key: set both in the store for every environment that serves downloads, redeploy that environment, repeat step 10.

A token cannot be minted by an agent. The owner creates it once and pipes it into the store.

## When a step fails

| Step | Failure | Do |
|---|---|---|
| 1 | tag already on another commit | move to a new version; never move a tag |
| 4 | identity not in keychain | list `security find-identity -v -p codesigning`, compare with the pinned SHA-1 |
| 5 | notary `Invalid` | `notarytool log <id>`; fix the named binary (usually a nested helper without hardened runtime) and rebuild |
| 5 | notary hangs | Apple has no SLA; wait, then resubmit once |
| 6 | no signature in output | wrong key account; fix before upload, a missing `.sig` breaks every installed app silently |
| 8 | several candidate files match a glob | delete leftovers from earlier builds; never take the first match |
| 8 | release already published | cut a new version instead |
| 10 | 503 from the route | the read token or repo is missing in that environment (above) |
| 10 | 204 or no update | asset name lacks the version/arch token the feed matches |

Every failure ends in a lesson: add the check to the script so the next release stops there, not after notarizing.

## Make it one command

If the project has no single script, write one that is steps 1 to 8 in order, takes the version as its only argument, has a `--dry-run` that stops before step 8, and dies on the first failed assertion with the fix in the message. Keep it one file. Repeat releases then cost one command plus steps 9 and 10.
