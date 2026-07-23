# API Surface

The current API is intentionally lightweight and file-backed. It follows the V1.1 requirement that Project, Canvas, Node, Edge, Run, Context Snapshot, and model state belong to this system rather than an external chat session.

## Project

`GET /api/projects`

Returns project metadata for the homepage.

`POST /api/projects`

Creates a project and its active canvas.

```json
{ "title": "New Canvas" }
```

`PATCH /api/projects/{project_id}`

Renames a canvas/project record. This is exposed both from the Index project
entry and from the active canvas title.

```json
{ "title": "Renamed Canvas" }
```

## Canvas

`GET /api/projects/{project_id}/canvas`

Returns the canvas graph:

```json
{
  "canvas": {
    "id": "project-id",
    "project_id": "project-id",
    "viewport": { "x": 0, "y": 0, "zoom": 1 },
    "nodes": [],
    "edges": [],
    "runs": [],
    "pinned_context": []
  }
}
```

## Interaction V2

`GET /api/projects/{project_id}/interaction`

Returns graph revision and the conversation-facing metadata: Scope records, conversation
sessions/messages, command proposals, and execution summaries. The canonical graph
itself remains available from the Canvas endpoint.

`GET /api/projects/{project_id}/scopes/{scope_id}/projection`

Returns the active graph projection for one Scope. The response contains only member
nodes and edges whose endpoints are both inside that scope; it never clones them into a
new canvas.

`POST /api/projects/{project_id}/scopes`

Creates a named `live` or `snapshot` Scope. A selector supports `all`, `explicit`, or
`neighborhood` membership rules.

`POST /api/projects/{project_id}/conversations`

Creates a conversation session with a title, `control_policy` (`manual`, `propose`,
`confirm`, or future `auto`), and active Scope.

`POST /api/projects/{project_id}/conversations/{session_id}/messages`

Appends a user, assistant, or system message. Messages store their Scope and optional
node references; they do not mutate graph nodes.

`POST /api/projects/{project_id}/conversations/{session_id}/guide-actions`

Advances the default deterministic Four Futures entry guide. `begin` accepts the
first topic, `answer` writes the current short answer to the canonical Research Brief
node, `skip` leaves an optional field empty, and `confirm_keywords` unlocks the
four-What-if stage. `set_start_mode` switches between `research` and `design` before
the topic is entered.

```json
{ "action": "answer", "body": "Public-space consent and refusal" }
```

This endpoint does not choose a tool, invoke a model, or create an image. It changes
only graph-owned brief/keyword nodes and the linked session's guide/progress state.

`POST /api/projects/{project_id}/command-proposals`

Creates an auditable proposal for a future graph change. Supported action values are
`create_node`, `patch_node`, `connect_nodes`, and `create_scope`.

`POST /api/projects/{project_id}/command-proposals/{command_id}/resolve`

Accepts `{ "resolution": "approved" }` or `{ "resolution": "rejected" }`.
Approval currently records reviewer intent only; no proposal applies a node mutation
until an explicit command executor is added.

All graph, interaction, and run mutation bodies may include `expected_revision`. It is
compared with the current canvas revision to prevent silent last-write-wins updates.

## Foundation Workflow

`GET /api/workflow-definitions`

Returns backend-owned workflow manifests. Definitions describe stages and required
input only; they do not contain model prompts, tool theory, or a duplicate graph.

`POST /api/projects/{project_id}/workflows`

Starts `workflow.four-futures-foundation` from an editable research brief.

```json
{
  "definition_id": "workflow.four-futures-foundation",
  "start_mode": "research",
  "topic": "Public-space speech recognition and the right to refuse",
  "research_focus": "How consent is communicated in shared space",
  "assumptions": ["Convenience is the default"],
  "stakeholders": ["Passers-by", "Operators"],
  "tensions": ["Safety and silence"]
}
```

This deterministic action creates a Research Brief node, a keyword-scaffold node, an
`operation.guided-scenario` node with direct data edges, a foundation Scope, and one
ConversationSession. It does **not** call a model, choose a tool, run an operation, or
create an image.

Pass an existing `session_id` with the start body to reuse the active conversation
instead of creating a second thread. The conversation guide uses this route internally
with `guided: true`; clients should normally use `guide-actions` for the default flow.

`POST /api/projects/{project_id}/workflows/{workflow_id}/select-branch`

Selects one current Guided Scenario branch after its four outputs have been generated.

```json
{ "branch_node_id": "node-branch" }
```

The API moves the linked ConversationSession into that branch's existing snapshot
Scope and activates its discussion step. It rejects a branch that is absent, belongs to
another workflow, or is stale. Editing a workflow source node after branch generation
marks all corresponding branches stale, requiring a new run before selection. Deleting
or editing a generated branch also clears the workflow's selection and records an
activity message in the linked conversation.

## Nodes

`POST /api/projects/{project_id}/nodes`

Creates a text, conversation, upload, image, multimodal, Modify, or manifest-driven
Operation node.

```json
{
  "type": "modify",
  "title": "Modify",
  "position": { "x": 320, "y": 160 },
  "payload": {},
  "config": {}
}
```

`PATCH /api/projects/{project_id}/nodes/{node_id}`

Updates position, size, status, payload, or config.

Graph mutation bodies may include `session_id`. When supplied, non-layout node edits
are written as linked activity messages in that conversation. Workflow-owned source
or branch edits invalidate dependent future branches rather than leaving them live.
Editing the canonical Research Brief also rebuilds its Keywords node from the current
Brief (and replaces a previous guided structured brief when the user edits free text),
then returns the linked conversation to `scope-global`.

`DELETE /api/projects/{project_id}/nodes/{node_id}`

Deletes one node and removes attached edges. If related runs reference the deleted
node as an executor or direct input, those run records are removed and dependent
outputs are marked stale when needed. The frontend exposes this through the node
right-click menu.

For a workflow-owned source, operation, or future branch, deletion also marks the
workflow stale and clears any selected branch. Send `expected_revision` and optional
`session_id` in the JSON DELETE body.

## Edges

`POST /api/projects/{project_id}/edges`

Creates a directed edge.

```json
{
  "source_node_id": "node-a",
  "target_node_id": "node-b",
  "source_port": "out",
  "target_port": "in",
  "edge_kind": "data"
}
```

For a manifest-defined Operation, `target_port` must be one of the operation
definition's declared input ports (for example, Guided Scenario uses `research`, not
`in`). The backend validates the port's accepted modalities, cardinality, and required
ports before a run.

Supported `edge_kind` values follow the requirement document:

- `data`
- `reference`
- `control`
- `configuration-reference`

Frontend operation: drag from a node's right output port to another node's left
input port. To delete one edge, right-click the edge line and choose `Delete`.

`DELETE /api/projects/{project_id}/edges/{edge_id}`

Deletes one directed edge without deleting either connected node.

For a Four Futures operation's direct `data` inputs, adding or removing an edge makes
the current workflow stale. Its run endpoint then refuses input sets that no longer
match the workflow's recorded canonical input set.

## Model Operations

`POST /api/projects/{project_id}/nodes/{node_id}/run`

Runs a Modify node or a runnable manifest-defined Operation through the backend executor. In the default deployment mode, the
request must include the visitor's key in the `X-Speculative-Web-Api-Key` header. The
key is used only for this run and is never included in the JSON body or response. If
`SPEC_WEB_ENABLE_OPENAI_RUNS` is not disabled, this endpoint calls OpenAI from the
server process. If model runs are disabled, it creates a placeholder output for local
tests and offline development. It creates:

- one `Run`
- one output node matching `config.output_type`
- one data edge from Modify to output
- a context snapshot containing direct input node IDs, selected tool IDs, and tool contracts
- the requested output type and the output recommendation snapshot
- a model snapshot containing provider, API path, and model name, but never secrets

The response language is inferred from the dominant language of the direct research
input. Researchers do not need to add language instructions or speculative-design
method terms to their node text. The interface itself can be switched between
Chinese and English without changing node content.

Graph editing endpoints intentionally do not generate content. Node creation, node movement, edge creation, tool toggles, and output-format changes only update graph state. Generation starts only at this Run endpoint.

### Guided Scenario Run

`operation.guided-scenario` requires at least one direct `data` input. Its backend
executor snapshots the `dators-four-futures` and `what-if` packages, then creates four
text branch artifacts and four snapshot Scopes: `growth`, `collapse`, `discipline`, and
`transformation`. Each artifact contains a What-if, a future premise, actors, tension,
visual brief, opening question, role prompts, and summary lenses. The response returns
`output_nodes`, `edges`, and `scopes` rather than one generic output node.

If model execution is unavailable or malformed, the operation creates an explicitly
marked template fallback. Inspect `run.model_snapshot.fallback_used` and
`fallback_reason`; do not treat this result as generated model content.

When this operation belongs to a Four Futures Foundation workflow, the same Run also
creates a comparison Scope for all four branch artifacts and advances the linked
session to explicit selection. A standalone Guided Scenario operation keeps its
existing behavior and creates only the four isolated branch Scopes.

`GET /api/projects/{project_id}/nodes/{node_id}/output-recommendation`

Returns the current public output recommendation for a Modify node. The
recommendation is derived from selected tool packages and input modalities.
Each selected tool keeps its own recommendation item so the UI can show
per-tool guidance without exposing internal package analysis fields.

```json
{
  "recommendation": {
    "type": "multimodal",
    "readiness": "mixed",
    "reason": "Selected tools have separate output recommendations; review each tool before running.",
    "warnings": [],
    "items": [
      {
        "tool_id": "what-if",
        "label": "What-If Scenarios",
        "type": "text",
        "readiness": "high",
        "reason": "What-If works best as a first written scenario seed.",
        "warnings": []
      }
    ]
  }
}
```

Modify `config.output_type` supports:

- `text`
- `image`
- `multimodal`

## Tools And Model

`GET /api/modifier-tools`

Returns placeholder Modify tools and output types for the UI.

`GET /api/operation-definitions`

Returns installed operation-node definitions from `operation_definitions/*/manifest.json`.
Definitions are independent from speculative tool packages and describe node ports,
output profiles, tool-selection policies, and execution capabilities.

`GET /api/model/status`

Reports backend model capability configuration, run enablement, and selected model
status without exposing secrets.

## Images

`POST /api/images/upload`

Accepts `multipart/form-data` with `file`. Supports JPEG, PNG, WEBP, and GIF. The response contains a local `image_url`, `image_file`, MIME type, and filename. Store those fields on an Image node, then connect that node directly to Modify to include the visual reference in the active model run. The current runtime sends at most four eligible app-owned images per model request.

Generated image and text+image output nodes include `visual_basis`, with the conclusion and evidence-node references used to derive their image prompt. Raw image bytes are never persisted in canvas JSON.

## Documents

`POST /api/documents/inspect`

Accepts `multipart/form-data` with `file`. Supports PDF, DOCX, TXT, and MD.

`POST /api/documents/render`

Accepts `multipart/form-data` with `file`. Supports PDF and DOCX rendering to PNG for visual QA.
