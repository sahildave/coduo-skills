---
name: coduo-install-on-phone
description: |
  Build the app and install it on the project's real test phones, one or
  several, then hand the user what to test. Reads which phones and which
  build command from the project's AGENTS.md, and writes that section the
  first time. Use for "install on my phone", "install on both phones",
  "reinstall on both iPhones", "put this build on your partner's phone", "give me
  what to test on device", and any manual QA that needs a camera, real touch,
  haptics, speech or a second device. Simulators are not this skill.
disable-model-invocation: false
---

# Coduo install on phone

A phone walk is where the user's time goes, so every minute they spend
installing, finding a stale build, or working out what to tap is a minute of
QA gone. The job: **the right build, on the right phones, verified, and a
checklist that starts from a real command.**

## 1. Read the project's phone setup

Look for `## Install on phone` in the repo's `AGENTS.md`. It holds:

- **Phones**: which ones, by the names `xcrun devicectl list devices` prints
  ("The owner's iPhone Pro", "your partner's iPhone"). Names, not UDIDs, because the
  file is committed and the names resolve on any machine the phones are
  paired to.
- **Build**: the build command and the path where the `.app` ends up.
- **Serve**: for a project with a dev server (Expo), the command that
  starts it.
- **Bundle id.**

If the section is missing, work it out. `project.yml` or an `.xcodeproj` means
native: `xcodebuild … -destination 'generic/platform=iOS'`. An `app.json`
with Expo means `bunx expo run:ios --device "<name>"` to build, and
`bunx expo start --dev-client` to serve. Then ask one question: which phones
does this project test on? A two-device app (pairing, connecting) needs every
phone. Most apps need one. Write the section into `AGENTS.md` and tell the
user it is there, uncommitted.

If the user names phones in the request ("just mine"), that overrides the
section for this run.

**Done when** you have the phone names, the build command, the `.app` path
and the bundle id.

## 2. Resolve the phones

```bash
xcrun devicectl list devices
```

Match each name. It must be `available (paired)` or `connected`. If a phone
is missing or unavailable, say which one and carry on with the rest instead of
stopping the whole walk. For device logs, a phone also has to be on a USB
**data** cable: `devicectl device info details` reporting
`transportType: localNetwork` means no syslog.

## 3. Build once, install everywhere

Build one `.app`, then install that same binary on every phone. Two builds
are two chances to test different code.

```bash
<build command from the section>
xcrun devicectl device install app --device <identifier> <path/to/App.app>
xcrun devicectl device process launch --device <identifier> <bundle id>
```

- **A locked phone** fails `launch` with `RequestDenied`. Ask the user to
  unlock it and retry. The install itself went through.
- **Installing over a different build of the same app can wipe its
  permissions** (camera, microphone, photos), for example a Debug build over
  a Release one. So install first and grant permissions after, and never
  install between granting a permission and retesting it. Record the install
  time; the checklist uses it.

**Done when** the version on each phone matches the build you just made.
Check it on the device, not by reading `Info.plist` in `/tmp`:

```bash
xcrun devicectl device info apps --device <identifier> --bundle-id <bundle id>
```

A stale binary makes a correct fix look broken and costs a whole diagnosis
round, so a phone you could not verify is reported as unverified.

## 4. Hand over the walk

In this order, with one fenced `bash` block per runnable step:

1. **Installed**: each phone, its version, and the install time.
2. **Serve**: the dev-server command, if the project has one.
3. **Starting state**: how to reach the state the walk needs. If the state
   can be reached by tapping, set up everything up to the step before it, so
   the user sees the transition happen instead of finding it already done.
4. **Checks**: numbered, one behaviour each, naming which phone does what
   when there are two. Each says what they should see.
5. **Logs, if the walk may need them**: say up front what the device log
   can and cannot show. On iOS, an app's `.info` and `.debug` lines are never
   persisted. When the device log tools come back empty, capture with
   `xcrun devicectl device sysdiagnose --device <identifier> --destination <dir> --gather-full-logs`
   and read the archive with `/usr/bin/log show`. In the agent shell, plain
   `log` resolves to something else and silently prints nothing.
