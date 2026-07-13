# Development Log - 2026-07-09

## Scope

Reviewed and hardened the current speculative design graph web prototype after the initial architecture build. The review focused on API key safety, Modify/tool extensibility, graph runtime clarity, and whether the current structure will support later interaction development.

## Architecture Understanding

The app is currently organized as a local Python HTTP service plus static HTML/CSS/JS frontend.

- Homepage: create canvases and open existing canvases.
- Canvas: render graph nodes, edges, zoom, connection interaction, document intake, model status, and Modify controls.
- Modify node: stores selected tools and requested output type. It does not generate content until `Run` is clicked.
- Backend graph store: persists projects, canvases, nodes, edges, runs, and context snapshots as JSON files.
- Model service: only reports backend configuration status for now; real OpenAI calls should be added behind the Run endpoint later.

## Security Review

Current API key handling is safe for this prototype:

- `OPENAI_API_KEY` is only read from backend environment variables.
- No frontend file contains an API key or receives the key value.
- `/api/model/status` exposes only a boolean configuration status and planned capabilities.
- The frontend calls backend endpoints only; it does not call OpenAI directly.

Issues found and fixed:

- Static path traversal risk: `static/../...` style paths could resolve outside the intended static directory. Static routing is now constrained to the resolved `static/` folder.
- Local path exposure: `/api/health` previously returned the project root path. It now omits the absolute local path.
- Missing request size boundaries: JSON and document upload requests now use configurable size limits from `server/config.py`.
- Graph integrity risk: edges could be created with missing source/target nodes. Edge creation now validates endpoint existence and edge kind.
- Unsupported node types could enter the store. Node normalization now rejects unknown node types.

Remaining prototype-level limits:

- There is no authentication or multi-user authorization yet. This is acceptable for local development, but must be revisited before any network/shared deployment.
- Uploaded documents are stored locally under `data/uploads`. Later builds should add cleanup/retention rules.
- File-backed JSON storage is simple and inspectable, but not enough for concurrent editing or large canvases.

## Tools Extensibility Review

The Modify tool layer is now flexible enough for the next development phase:

- Default tools live in `server/modifier_registry.py`.
- The registry exposes tool list, output types, tool snapshots, output recommendations, and output-to-node mapping.
- Existing canvas nodes are normalized on read/write, so old Modify nodes receive current registry labels and versions.
- Optional `data/tool_registry.json` can override Modify tools without changing frontend code.
- The frontend renders `node.config.tools`, so it does not need to know the final tool list in advance.

Recommended next step for real tools:

1. Keep registry metadata in `modifier_registry.py` or `data/tool_registry.json`.
2. Add a separate executor layer for actual tool behavior.
3. Let `run_modify` call the executor only after collecting context, selected tools, output type, and model configuration.
4. Store executor/model snapshots in the Run object for provenance.

## Interaction Development Review

The current interaction foundation is usable:

- Nodes can be added and rendered by type.
- Ports create directed edges.
- Edges are calculated from node ports, reducing visual offset issues.
- Canvas zoom is bounded from 25% to 100% and works with wheel/trackpad.
- Canvas grid is removed; the workspace is a simple framed surface.
- Light/dark mode uses black/white CSS variables only.
- UI labels are English, while text node content can contain Chinese or other user input.

Potential friction points for upcoming work:

- `static/app.js` is growing into a large single file. Before interactions become complex, split it into modules such as graph rendering, graph actions, API client, theme, and node renderers.
- There is no selection model yet. Editing, deleting, copy/paste, inspector panels, and keyboard shortcuts will be easier after introducing `selectedNodeId` / `selectedEdgeId`.
- There is no explicit node schema registry yet. If many node types are added, create a `node_registry.py` backend module and a matching frontend renderer registry.
- Viewport pan/scroll state is not persisted yet. Zoom is read from canvas state, but not patched back to storage.
- The Run endpoint still creates placeholder output. Real OpenAI integration should stay server-side and should never expose request credentials or raw secrets to the frontend.

## Files Changed In This Pass

- `app.py`: safer static routing, request body limits, cleaner health response, better graph mutation errors.
- `server/config.py`: size limit and tool registry file configuration.
- `server/graph_store.py`: node type validation, edge kind validation, endpoint validation, Modify config normalization.
- `server/modifier_registry.py`: default registry plus optional `data/tool_registry.json` override.
- `tests/test_graph_store.py`: coverage for invalid node and edge rejection.
- `docs/architecture.md`: added security boundaries and tool registry notes.

## Verification

Run after changes:

- `tests/run_tests.py`
- `scripts/check_visual_tokens.py`
- `scripts/smoke_test.py`

All passed.

## Follow-up Interaction And Tool Package Pass

Additional fixes from canvas testing:

- Preserved current canvas zoom and scroll position when adding nodes, toggling Modify tools, changing output type, editing text, or running Modify. Opening a different canvas still initializes from that canvas viewport.
- Clarified the context menu target: right-click/two-finger-click an edge opens an edge menu and `Delete Edge`; right-click a node opens a node menu and `Delete Node`.
- Moved speculative-design method responsibility out of user text nodes. Text and conversation nodes are treated as research material, user intent, preferences, or local instructions. Modify now explicitly tells the model that selected tool packages supply the method logic.
- Updated the sample scientific workflow so it no longer asks the scientist user to write a `Design Fiction Brief`.
- Added modular tool packages for `Futures Triangle`, `Futures Wheel`, `Dator's Four Futures`, `Causal Layered Analysis`, `Experiential Futures Ladder`, `Envisioning Cards`, and `Three Horizons`, with manifests, theory notes, schemas, constraints, evaluators, and examples.
