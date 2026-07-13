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

## Nodes

`POST /api/projects/{project_id}/nodes`

Creates a text, conversation, upload, image, multimodal, or Modify node.

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

`DELETE /api/projects/{project_id}/nodes/{node_id}`

Deletes one node and removes attached edges. If related runs reference the deleted
node as an executor or direct input, those run records are removed and dependent
outputs are marked stale when needed. The frontend exposes this through the node
right-click menu.

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

Supported `edge_kind` values follow the requirement document:

- `data`
- `reference`
- `control`
- `configuration-reference`

Frontend operation: drag from a node's right output port to another node's left
input port. To delete one edge, right-click the edge line and choose `Delete`.

`DELETE /api/projects/{project_id}/edges/{edge_id}`

Deletes one directed edge without deleting either connected node.

## Modify Run

`POST /api/projects/{project_id}/nodes/{node_id}/run`

Runs a Modify node through the backend executor. If `OPENAI_API_KEY` is configured and
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

`GET /api/model/status`

Reports backend model capability configuration, run enablement, and selected model
status without exposing secrets.

## Documents

`POST /api/documents/inspect`

Accepts `multipart/form-data` with `file`. Supports PDF, DOCX, TXT, and MD.

`POST /api/documents/render`

Accepts `multipart/form-data` with `file`. Supports PDF and DOCX rendering to PNG for visual QA.
