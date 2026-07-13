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

## Modify Pipeline

1. Upstream `data` edges define direct inputs.
2. Modify config stores selected tool IDs and requested output type.
3. `server/modifier_registry.py` normalizes tool snapshots and output recommendations.
4. `run_modify` builds the model prompt from direct inputs, selected tool contracts, requested output type, output recommendation, and inferred response language.
5. `run_modify` records a context snapshot, model snapshot, produced output node, and provenance edge.

This keeps future tool integration localized: add tool definitions and execution constraints to the registry/executor, then keep the canvas UI focused on graph editing.

User content nodes are research material, user intent, source context, or local instructions. They should not be treated as the place where a scientist user must write a "design fiction brief" or know speculative-design method language. Modify owns the method translation: selected tool packages provide theory mappings, input/output contracts, model constraints, and validation rules that convert research inputs into speculative outputs.

The `中文` / `EN` interface switch is a presentation preference stored in browser local storage. It translates interface chrome and system defaults only; it never alters existing research text, generated content, canvas titles, or tool-package source material.

## Tool Constraint Flow

The architecture supports iterative tool/theory mapping.

- Tool metadata can describe `accepted_modalities`, `supported_outputs`, `input_contract`, `output_contract`, `theory_mapping`, `model_constraints`, `parameters`, `validation`, and future `executor` settings.
- Tool package folders under `tool_packages/` are the canonical place for theory notes, schemas, constraints, evaluator prose, and examples. The frontend should only render the normalized registry view.
- Modify nodes store a normalized snapshot of currently available tools, so the UI can render new or revised tools without hardcoding them.
- Runs store a `tool_snapshot`, so generated output can later be traced back to the exact tool version and constraints used at generation time.
- `data/tool_registry.json` can override the default registry while keeping frontend code unchanged. Use `data/tool_registry.example.json` as the editable template.
- Future Modify-like operation nodes should follow the same pattern: registry metadata, node config snapshot, executor call only from the Run endpoint, and run-level provenance.

## Security Boundaries

- Each browser tab requires a visitor-supplied API key before it can run a Modify node. The frontend holds that key in JavaScript memory only and clears the form field immediately after acceptance; it is not stored in browser storage, cookies, URLs, canvas JSON, run snapshots, or status responses.
- The run request sends the key only as the same-origin `X-Speculative-Web-Api-Key` header. `app.py` rejects a model run without that header when `SPEC_WEB_REQUIRE_USER_API_KEY=1`.
- OpenAI calls happen only inside `server/model_service.py`. The run-specific key is passed through the executor only for the active request and is never persisted or logged by this application.
- The frontend reads `/api/model/status`, which exposes only run enablement, model status, and broad capabilities, never secrets.
- API responses are marked `Cache-Control: no-store`; browser responses include CSP, frame denial, referrer, and content-type protections. HSTS is sent on HTTPS-forwarded requests.
- Static file routing is scoped to `static/` and rejects path traversal outside that directory.
- JSON and document upload request bodies have size limits in `server/config.py`.
- Graph mutation validates node types, edge kinds, and edge endpoint existence before writing canvas data.

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
