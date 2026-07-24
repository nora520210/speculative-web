# Architecture Notes

This prototype is organized around a graph runtime rather than a chat page.

## Surfaces

- `static/index.html`: homepage and canvas workspace shell.
- `static/app.js`: graph interaction, node rendering, connection creation, zoom, theme and interface-language toggling, API calls.
- `static/styles.css`: black/white experimental visual system with light and dark variable sets.
- `app.py`: stdlib HTTP API and static file server.
- `api/index.py`: Vercel serverless entrypoint that reuses the HTTP handler.
- `server/graph_store.py`: file-backed projects, canvases, nodes, edges, runs, and runtime snapshots.
- `server/modifier_registry.py`: placeholder Modify tools, output types, output recommendations, and output-node mapping.
- `server/model_service.py`: backend-only OpenAI status, model selection, Responses API calls, and Chat Completions fallback.
- `server/documents.py` and `server/rendering.py`: document intake and render helpers.

## Runtime Rule

Canvas editing does not generate content.

- Creating nodes does not call the model.
- Moving nodes does not call the model.
- Connecting nodes does not call the model.
- Selecting Modify tools does not call the model.
- Choosing `Text`, `Image`, or `Text+Image` output does not call the model.

Only `POST /api/projects/{project_id}/nodes/{node_id}/run` is allowed to create generated output. With `OPENAI_API_KEY` configured, this endpoint calls OpenAI from the backend. Tests and offline development can set `SPEC_WEB_ENABLE_OPENAI_RUNS=0` to keep placeholder output.

## Interaction Architecture V2

The canvas remains the one canonical graph. Conversation is a coordinated surface over
that graph, never a second canvas that copies nodes.

- `Scope` is a named graph projection. It can select every node, explicit node IDs, or
  a bounded neighbourhood; a scope can be `live` or retain a node-ID snapshot. A
  projection returns only the selected nodes and their internal edges.
- `ConversationSession` stores messages, a current scope, an adjustable control
  policy, progress steps, and a small deterministic `guide` cursor. Messages reference
  node IDs and scopes; they do not duplicate node content into a parallel graph. A
  message may be ordinary conversation, a guide prompt, or a graph `activity` record.
- `CommandProposal` represents an intended graph action such as `create_node`,
  `patch_node`, `connect_nodes`, or `create_scope`. Its lifecycle is
  `proposed -> approved | rejected -> applied`.
- The V2 UI exposes the first two resolution states only. Approving a proposal does
  **not** mutate graph nodes yet. This preserves the deliberately undecided boundary
  around direct conversational control while giving the future executor a stable,
  auditable input contract.
- `Execution` is the durable shell around a Run. It records context, model, and
  materialisation steps. Current Modify generation remains synchronous; an async job
  worker/SSE event stream can replace that executor without changing the Canvas,
  Scope, Conversation, or Command contracts.

The canvas contains additive V2 fields alongside the existing `nodes`, `edges`, and
`runs` fields:

```json
{
  "schema_version": 2,
  "revision": 12,
  "scopes": [],
  "conversation_sessions": [],
  "workflow_instances": [],
  "command_proposals": [],
  "executions": [],
  "events": []
}
```

Graph mutations accept an optional `expected_revision`. A stale revision receives a
conflict instead of silently overwriting a newer canvas. The file store now writes JSON
atomically for local development. It is still a local prototype adapter: production
collaboration and worker execution need a transactional database plus object storage.

### Focused Conversation Workspace

The canvas interface is a quiet research workspace with four persistent regions:

1. A 72px full-height left rail exposes direct node creation, the Four Futures entry
   point, zoom, and the tools selected by Modify nodes as compact symbols. It is a
   launcher, not a second content panel.
2. The upper-left region renders the active Scope projection, not the entire graph;
   a new guided thread begins in `scope-current-inquiry` when that local Scope exists.
   Untouched historical demo sessions with the former global entry are migrated to this
   same local start without changing authored conversations or workflows.
3. The upper-right region is a persistent global-map navigator. Selecting a Scope
   changes the focused projection; it never creates or copies a second canvas.
4. The lower region is the linked conversation session. Its entry state suppresses the
   progress strip and message history: it shows one default-path hint, one optional
   mode switch, and the input. Contextual prompts appear only when a guide stage needs
   a decision.

System, guide, activity, and assistant messages are capped to 200 characters by the
runtime before persistence and are capped again by the presentation layer for legacy
data. User research input is not shortened (up to the normal message storage limit).
This keeps feedback scannable without losing source material.

The layout is only a projection of canonical Scope, graph, and conversation state.
Selecting a Scope from the navigator performs a revision-checked update of the linked
conversation session before reloading the graph projection. The graph and conversation
therefore share one active Scope; visual cards do not introduce a second interaction
state.

### Extensible Operation Nodes

`Modify` remains compatible with existing canvases, but it is no longer the only
possible operation shape. `operation_definitions/*/manifest.json` defines an operation
node through its stable ID/version, category path, typed input ports, output profiles,
tool-selection rules, execution contract, and presentation hints. The initial
`operation.transform` definition is intentionally generic.

An `operation` node stores a `definition_ref`, parameter values, tool selections, and
an output profile. Adding a future operation family therefore means adding a manifest
and executor implementation rather than extending frontend conditionals or forcing a
new tool hierarchy into Modify. Tool packages continue to own theory, contracts,
constraints, evaluators, and versions; operation definitions only describe how a graph
node may select and execute them.

### Guided Scenario Operation

`operation.guided-scenario` is the first runnable operation-node family. It adapts the
reviewed guided-agent workflow without importing its client-side phase machine:

1. It resolves only direct `data` inputs from the graph.
2. It snapshots the installed `dators-four-futures` and `what-if` tool packages.
3. Its backend executor generates—or, in offline mode, transparently templates—four
   ordered branches: growth, collapse, discipline, and transformation.
4. Each branch becomes a separate text artifact and a snapshot Scope containing only
   its direct research inputs and itself. No branch is selected or discussed
   automatically.
5. The branch artifact carries an opening question, researcher/designer role prompts,
   and summary lenses. A later conversation operation can use these as input without
   duplicating conversation state into the node.

The Run records the definition/version, direct input IDs, exact package snapshots,
output node IDs, model/fallback metadata, and the four branch Scope IDs. A fallback is
always marked in `model_snapshot.fallback_used`; it is never presented as
model-generated content.

### Four Futures Foundation Workflow

`workflow_definitions/*/manifest.json` defines a reusable interaction sequence over
the existing graph runtime. A workflow instance contains only references to canonical
node IDs, Scope IDs, one ConversationSession, and its current stage. It never stores a
second copy of research content or a client-side phase machine.

The initial `workflow.four-futures-foundation` introduces the lower-cognitive-load
path requested for the early and middle research process:

1. Capture either a researcher-led inquiry or a designer-led proposition as one
   editable Research Brief.
2. Create a deterministic, editable keyword scaffold next to that brief. This is
   intentionally not a model call.
3. Prepare the existing `operation.guided-scenario` with direct data edges from the
   brief and keywords. Starting the workflow does not select a tool, call a model, or
   produce an image.
4. When that operation is later run, move the linked conversation into a comparison
   Scope containing all four results. The existing Four Futures executor keeps its
   canonical `growth`, `collapse`, `discipline`, and `transformation` strategies.
5. Require an explicit human branch selection before the conversation enters that
   branch's isolated Scope. Only then does the workflow become a focused discussion.

If either workflow input is edited after branch generation, the workflow and its old
branch artifacts become `stale`. The user must run the four futures again rather than
discussing a silently out-of-date result. This sequencing changes interaction state,
not the model, image, or tool-selection mechanism, so those systems can evolve later
without replacing the workflow contract.

### Conversation-first, Node-equivalent Control

The default Working Thread starts with a deterministic guide rather than a blank
chat. It asks for the topic, focus, assumptions, stakeholders, and tensions in small
steps. Each answer is written directly into the owned Research Brief node and then
rebuilds the editable keyword scaffold from that same node. There is no hidden chat
copy of the brief. A direct text edit to the Brief explicitly supersedes its old
structured guide object and deterministically rebuilds the Keywords node, so later
What-if runs cannot combine a new brief with old keywords.

The user can at any time take the equivalent node route: edit a node, connect or
remove an edge, delete a branch, or select a branch from the graph. Semantic graph
changes append an `activity` message to the linked conversation session with node
references. Layout-only moves do not create noise in the timeline.

For a workflow-owned Guided Scenario operation, `source_node_ids` and
`input_edge_ids` record the semantic direct `data` inputs and their provenance at
workflow creation. Adding, removing, editing, or deleting a managed input—or deleting/editing
a generated branch—marks the workflow stale, clears any selected branch, returns the
session to a safe global scope, and records why. The operation refuses to run against
a different set of graph inputs. This makes dialogue control and direct node control
two synchronized entrances to the same dataflow instead of two competing state
machines.

Every manifest-defined Operation also owns its data-port contract: an incoming edge
must name a declared port, provide an accepted modality, respect the port cardinality,
and satisfy required ports before execution. The canvas reads the initial connection
port from that manifest; the backend repeats the validation as the authoritative
check. This keeps tool packages and operation definitions modular rather than placing
their contracts in the conversation or frontend layer.

## Modify Pipeline

1. Upstream `data` edges define direct inputs.
2. Modify config stores selected tool IDs and requested output type.
3. `server/modifier_registry.py` normalizes tool snapshots and output recommendations.
4. `run_modify` builds the model prompt from direct inputs, selected tool contracts, requested output type, output recommendation, and inferred response language.
5. `run_modify` records a context snapshot, model snapshot, produced output node, and provenance edge.

When direct input edges include Image or Text+Image nodes, the runtime creates a bounded visual context from up to four app-owned local image files. It sends the pixels only to the active vision-capable model request and stores only node IDs, image references, and MIME metadata in the graph. New generated images require a model-returned `visual_basis` containing a concise conclusion, direct evidence node IDs, and any real reference-image node IDs. The image prompt must be derived from that conclusion. Images without a local file, remote URLs, oversized files, and images beyond the request limit are not represented as visual evidence.

This keeps future tool integration localized: add tool definitions and execution constraints to the registry/executor, then keep the canvas UI focused on graph editing.

User content nodes are research material, user intent, source context, or local instructions. They should not be treated as the place where a scientist user must write a "design fiction brief" or know speculative-design method language. Modify owns the method translation: selected tool packages provide theory mappings, input/output contracts, model constraints, and validation rules that convert research inputs into speculative outputs.

The `中文` / `EN` interface switch is a presentation preference stored in browser local storage. It translates interface chrome and system defaults only; it never alters existing research text, generated content, canvas titles, or tool-package source material.

## Tool Constraint Flow

The architecture supports iterative tool/theory mapping.

- Tool metadata can describe `accepted_modalities`, `supported_outputs`, `input_contract`, `output_contract`, `theory_mapping`, `model_constraints`, `parameters`, `validation`, and future `executor` settings.
- Tool package folders under `tool_packages/` are the canonical place for theory notes, schemas, constraints, evaluator prose, and examples. The frontend should only render the normalized registry view.
- Modify nodes store a normalized snapshot of currently available tools, so the UI can render new or revised tools without hardcoding them.
- Runs store a `tool_snapshot`, so generated output can later be traced back to the exact tool version and constraints used at generation time.
- Each package may additionally carry an optional `presentation` object, validated by
  `tool_packages/presentation.schema.json`. It owns card family, icon/accent tokens,
  package-relative graphic assets, compact fields, and an interaction hint. The
  frontend renders normalized presentation metadata but cannot use it to change a
  package's theory, input/output contract, or executor. This keeps future graphical
  tool cards coupled to the selected package rather than duplicated in UI conditionals.
- `data/tool_registry.json` can override the default registry while keeping frontend code unchanged. Use `data/tool_registry.example.json` as the editable template.
- Future Modify-like operation nodes should follow the same pattern: registry metadata, node config snapshot, executor call only from the Run endpoint, and run-level provenance.

## External Prototype Isolation

The reviewed external prototypes live under `7.22SPEC/` only as local reference
material. The directory is ignored by Git and no registry, module loader, static route,
or runtime glob reads from it. Production packages are discovered only from
`tool_packages/*/manifest.json`, operation definitions from
`operation_definitions/*/manifest.json`, and workflows from
`workflow_definitions/*/manifest.json`. This allows their interaction logic to inform
the implementation without importing their code, dependencies, state, or UI into this
system.

## Security Boundaries

- Each browser tab requires a visitor-supplied API key before it can run a Modify node. The frontend holds that key in JavaScript memory only and clears the form field immediately after acceptance; it is not stored in browser storage, cookies, URLs, canvas JSON, run snapshots, or status responses.
- The run request sends the key only as the same-origin `X-Speculative-Web-Api-Key` header. `app.py` rejects a model run without that header when `SPEC_WEB_REQUIRE_USER_API_KEY=1`.
- OpenAI calls happen only inside `server/model_service.py`. The run-specific key is passed through the executor only for the active request and is never persisted or logged by this application.
- The frontend reads `/api/model/status`, which exposes only run enablement, model status, and broad capabilities, never secrets.
- API responses are marked `Cache-Control: no-store`; browser responses include CSP, frame denial, referrer, and content-type protections. HSTS is sent on HTTPS-forwarded requests.
- Static file routing is scoped to `static/` and rejects path traversal outside that directory.
- JSON and document upload request bodies have size limits in `server/config.py`.
- Graph mutation validates node types, edge kinds, and edge endpoint existence before writing canvas data.
- Image uploads accept only JPEG, PNG, WEBP, or GIF under the upload size limit. The backend resolves only app-owned `uploads/` and `generated/` files for vision input; it does not fetch arbitrary remote URLs.
- Local storage persists reference images during development. The Vercel runtime uses ephemeral `/tmp` storage by default, so production workflows that need durable image inputs must configure persistent object storage behind the same upload/reference interface.

## Tool Registry

Modify tools have defaults in `server/modifier_registry.py`.

For future iteration, `data/tool_registry.json` can override the default list without changing the UI. Copy `data/tool_registry.example.json` when starting a custom registry. The expected shape is:

```json
{
  "modifier_tools": [
    {
      "id": "what-if",
      "version": "0.1.0",
      "label": "What-if",
      "accepted_modalities": ["text", "image", "multimodal"],
      "supported_outputs": ["text", "image", "multimodal"],
      "input_contract": {
        "required": ["source_claim_or_scenario"],
        "optional": ["domain_context"]
      },
      "output_contract": {
        "text": ["what_if_question", "transformed_scenario"],
        "image": ["visual_brief", "image_prompt"],
        "multimodal": ["written_brief", "visual_brief", "image_prompt"]
      },
      "theory_mapping": {
        "family": "speculative design",
        "method": "what-if reframing"
      },
      "model_constraints": [
        "Preserve traceability to the source input."
      ],
      "selected": true,
      "placeholder": true
    }
  ]
}
```

## API Key Access

The default deployment mode uses a visitor-owned API key rather than a shared server-side model budget. Every new page load displays the API access gate. The key is held only for that tab and sent only with a Modify Run header; reloads and tab closes clear it.

For trusted local development, an administrator may set `SPEC_WEB_REQUIRE_USER_API_KEY=0` and configure `OPENAI_API_KEY` in `.env`. Do not use that fallback for a public Vercel deployment.

## Vercel Runtime

`vercel.json` rewrites requests to the Python entrypoint. In local development data is written beneath `data/`; on Vercel, absent an explicit `SPEC_WEB_DATA_DIR`, the app uses `/tmp/speculative-web` so it can run inside the serverless filesystem. That directory is ephemeral and must be replaced with a database and object storage integration before persistent production use. The public deployment should keep `SPEC_WEB_REQUIRE_USER_API_KEY=1`, use Vercel HTTPS, and avoid configuring a shared production `OPENAI_API_KEY`.
