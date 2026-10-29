# Flow map JSON schema

One object, ten keys. `repository`, `description`, `nodes`, `edges`, and
`flows` are required; the rest sharpen the page.

```json
{
  "schemaVersion": "1.0.0",
  "repository": "Atlas",
  "description": "One line under the title, and the diagram's fallback subtitle.",
  "generatedFrom": ["docs/CODE-MAP.md", "src/", "api/"],
  "architecturalConstraints": ["Invariants a reviewer would reject a PR for breaking."],
  "knownIssues": [
    { "kind": "import-cycle", "path": ["a.ts", "b.ts", "a.ts"], "source": "docs/CODE-MAP.md" }
  ],
  "dashboardCapabilities": { "flowDiscovery": ["Search by flow label, operation, or source path"] },
  "layout": { "width": 1480, "height": 980, "lanes": [{ "y": 26, "label": "Entries and presentation" }] },
  "nodes": [],
  "edges": [],
  "flows": []
}
```

`generatedFrom`, `architecturalConstraints`, `knownIssues`, and
`dashboardCapabilities` are read by the next agent, not by the renderer. They
are the map's provenance: keep them true or drop them.

## nodes

One card on the canvas.

```json
{
  "id": "web-entry",
  "label": "Web entry",
  "layer": "runtime",
  "kind": "entry-point",
  "paths": ["src/entry-web.tsx", "src/WebApp.tsx"],
  "technology": ["React 19", "Vite"],
  "description": "Mounts the browser-only tree and stays free of native imports.",
  "responsibilities": ["Mount web providers", "Preserve the browser bundle boundary"],
  "position": { "x": 260, "y": 120 }
}
```

- `id` — stable, kebab-case. Flows and edges reference it; renaming one discards
  the human's stored QA ticks for any flow that names it.
- `label` — two or three words. The card is 184x58px and clips longer text.
- `layer` — the horizontal band and the colour. Colours are assigned per layer
  in first-appearance order, so any vocabulary works. A useful default set:
  `external`, `runtime`, `presentation`, `feature`, `application`, `state`,
  `domain`, `data`, `integration`, `platform`, `server`, `storage`, `native`,
  `tooling`. Reuse one layer name for every node in the same band.
- `kind` — the role within the layer (`actor`, `entry-point`, `shell`,
  `routing`, `feature-group`, `user-flow-controller`, `service`, `adapter`,
  `client`, `cache`, `store`, `port`, `external-service`, `toolchain`). Read by
  humans, not the renderer.
- `paths` — repo-relative files. They show in the hover tooltip and feed the
  dashboard's search, so a flow becomes findable by the file a reader is
  staring at. External systems have none; give them `technology` instead.
- `position` — see Canvas below.

## edges

One directed arrow. Edges are the graph; flows only traverse them.

```json
{
  "id": "e24",
  "source": "graphql-operations",
  "target": "github-api",
  "relation": "requests",
  "description": "Typed operations issue the network call.",
  "protocol": "HTTPS GraphQL"
}
```

- `id` — short and sequential (`e01`, `e02`). Flows list these.
- `relation` — a verb phrase, lowercase, read as `source <relation> target`
  ("mounts", "patches/rolls back", "implemented by"). It is the arrow's tooltip.
- `protocol` — the mechanism ("Tauri IPC", "TanStack Query", "HTTPS REST").

One edge per distinct relationship. When two flows use the same connection,
they share the edge id rather than each getting their own.

## flows

The dashboard's rows. Everything except `id`, `category`, `label`, `summary`,
and `steps` is optional, and each optional field renders its own block.

```json
{
  "id": "create-issue",
  "category": "user",
  "label": "Create an issue",
  "summary": "Create the issue, add it to the project, and apply project fields without blocking the composer.",
  "trigger": "Submit ComposeDialog from the board, sidebar, or command palette.",
  "steps": ["user", "compose-issue", "optimistic-cache", "mutation-service", "github-api"],
  "edgeIds": ["e59", "e60", "e61", "e62", "e24"],
  "operations": ["create-issue", "add-item-to-project", "set-field-value per selected field"],
  "successOutcome": "The composer clears, a pending card appears, and its temp id swaps to the real one.",
  "failureBehavior": "The pending card is removed and stage-aware Retry resumes without a duplicate issue.",
  "sourcePaths": ["src/features/compose/ComposeDialog.tsx"],
  "qa": {
    "manual": [
      {
        "id": "pending-card",
        "label": "Submit a valid issue with the network throttled.",
        "expected": "The composer clears immediately and a pending card shows the composed title."
      }
    ],
    "automated": [
      {
        "label": "Composer and staged-create tests",
        "command": "npm run test:run -- src/features/compose/ComposeDialog.test.tsx",
        "paths": ["src/features/compose/ComposeDialog.test.tsx"]
      }
    ]
  }
}
```

- `category` — `user` or `system`. These are the dashboard's two filter tabs,
  and `user` is the default view.
- `steps` — node ids in narrative order, starting at the actor or trigger. This
  is the highlight set and the ordered "Path" list in the QA panel.
- `edgeIds` — the edges this flow traverses. They highlight in brand colour with
  a filled arrowhead. Cover every consecutive pair in `steps`; validate warns
  when a step no edge touches.
- `qa.manual[].id` — stable, kebab-case, unique within the flow. It keys the
  checkbox in browser storage.
- `qa.manual[].expected` — the observable result. Required by validate.

## Canvas

`layout.width` x `layout.height` (default 1480x980) is the SVG viewBox. Cards
are 184x58 and `position` is the top-left corner.

- **Flow runs left to right.** Actors and entry points on the left, external
  services on the right. A reader should be able to trace a journey without
  backtracking.
- **Layers stack in rows.** Nodes sharing a `layer` share a y band. Columns at
  x = 40, 260, 480, 700, 920, 1040, 1260 and rows 80px apart hold 184px cards
  with room for arrows.
- **Leave 8px of clearance.** Validate warns on cards closer than that.
- **`layout.lanes`** draw a labelled rule across the canvas at each `y` — one
  per band of rows, naming what that band is. Optional; without them the canvas
  is unlabelled but correct.

## What the renderer ignores

`schemaVersion`, `kind`, `responsibilities`, `edges[].description`,
`generatedFrom`, `architecturalConstraints`, `knownIssues`, and
`dashboardCapabilities` never reach the page. They exist for the agent that
maintains the map next. Everything else is rendered, searched, or both.
