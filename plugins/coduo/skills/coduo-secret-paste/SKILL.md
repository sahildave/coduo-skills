---
name: coduo-secret-paste
description: Store a secret the owner pastes into Infisical (and optionally Depot CI) without any agent seeing it. Use whenever the owner must paste an API key, token or password: "paste the key", "store this secret", a new provider token, a rotated credential.
---

# Coduo secret paste

`scripts/secret-paste` (next to this file) reads one hidden paste from a real terminal,
stores it in Infisical, reads it back to confirm, and prints only its length.

## Run it

Start it with the terminal tool (`run_in_terminal`), then tell the owner to paste in that tab:

```bash
~/.agents/skills/coduo-secret-paste/scripts/secret-paste KEY --env dev --path /products/<name> --project <infisicalProjectId>
```

Add `--depot owner/repo [--workflow file.yml]` to set the same value as a Depot CI secret.

- Never run it through Bash or tell the owner to use Claude Code's `!` prompt. Neither has a
  terminal, so the paste is lost; the script refuses rather than storing an empty value.
- Never read, print or ask for the value in chat. Name the key and its path only.
- To check it landed, list key names (`infisical secrets ... -o json | jq -r '.[].secretKey'`),
  never values.
- To copy a secret already in Infisical somewhere else, pipe it
  (`infisical secrets get --plain --silent | depot ci secrets set --from-stdin`) and never print it.
