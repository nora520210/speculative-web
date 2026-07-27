# Workflow package contract

Use one folder per workflow under `workflow_definitions/`. A workflow package is the
translation layer between a reviewed natural-language process document and the stable
graph runtime.

## Manifest owns

- Stable workflow id and version.
- Stage ids, order, labels, and descriptions.
- Required/optional start inputs.
- References to operation definitions.
- Tool-selection policy that references package ids only.
- Localized display copy for labels and stages.

## Manifest must not own

- CSS, DOM selectors, panel layout, card dimensions, or button locations.
- Tool theory, prompts, API keys, or model calls.
- A copied node graph or copied conversation content.

## Safe change path

1. Convert the proposed flow into a new manifest version.
2. Reuse existing graph contracts where possible; add a backend transition only for
   a real new graph/Scope/execution semantic.
3. Snapshot the definition on workflow creation.
4. Test both conversation-led and direct-node-led routes against the same canonical
   nodes and Scope transitions.
5. Keep the frontend generic: it reads workflow progress and the stored snapshot.
