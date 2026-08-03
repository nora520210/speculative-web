# Speculative Web

Node-based speculative-design workspace for scientific and engineering research teams. Researchers add feasible research directions or materials; the Modify node owns tool selection, response structure, language inference, and image constraints.

## Local Run

```bash
python3 -m pip install -r requirements.txt
PORT=8002 python3 app.py
```

Open `http://127.0.0.1:8002`.

Copy `.env.example` to `.env`. By default, the browser asks each visitor for their own API key before any model operation. A local `OPENAI_API_KEY` is optional only for trusted development when `SPEC_WEB_REQUIRE_USER_API_KEY=0`.

## API Key Access

Each new page load begins with an API-key access gate. The submitted key is kept only in the current browser tab's memory, is cleared on refresh or tab close, and is sent only with a Modify Run request in a same-origin request header. It is never put in browser storage, canvas data, run history, URLs, or server logs.

The key is checked when the user first runs a model operation. This is an access gate for a visitor-owned API key, not a user-account system.

## Interface Language

The compact `中文` / `EN` control in the top menu switches interface language and is saved locally in the browser. It intentionally does not translate research inputs, existing canvas titles, tool package theory, or generated content.

## Multimodal Evidence

An `Image` node can upload a JPEG, PNG, WEBP, or GIF reference. Connect several direct image and text nodes to a Modify node to give the model real visual and written context. The runtime sends at most four bounded local image inputs only for that active request; canvas JSON stores only node IDs and file references.

For image and text+image outputs, the model must return a `visual_basis` tied to direct upstream evidence and a specific image prompt derived from that conclusion. The system does not generate a new image from generic atmosphere or an empty prompt.

The current file-backed storage is suitable for local work. On Vercel, uploaded reference files and generated images use ephemeral runtime storage; use an object store through `SPEC_WEB_DATA_DIR` or a storage adapter before relying on image persistence across serverless instances.

## Vercel Deployment

This repository is prepared for Vercel's Python runtime:

1. Import the GitHub repository in Vercel.
2. Vercel detects `vercel.json`; no build command is required.
3. In **Project Settings -> Environment Variables**, set:
   - `OPENAI_IMAGE_MODEL=gpt-image-1`
   - `SPEC_WEB_ENABLE_OPENAI_RUNS=1`
   - `SPEC_WEB_REQUIRE_USER_API_KEY=1`
   - optionally `OPENAI_MODEL` for a fixed text model
4. Deploy and test `/api/health`.

The Vercel runtime uses `/tmp/speculative-web`, so canvases, uploaded documents, and generated image files are **ephemeral** there. The deployed site works within a warm runtime, but it must be connected to a durable database and object store before treating saved canvases as persistent production data. Do not configure a shared production `OPENAI_API_KEY` for the visitor-key flow or add a key to source files or browser-side code. Vercel supplies HTTPS; the app also sends browser security headers and no-store API responses.

## Checks

```bash
python3 tests/run_tests.py
python3 scripts/doctor.py
python3 scripts/smoke_test.py
```

## Structure

- `static/`: dependency-free interface and interaction layer.
- `server/`: graph store, model service, document parsing, and dynamic tool registry.
- `tool_packages/`: independent theory and output-contract packages discovered by the backend.
- `api/index.py`: Vercel serverless entrypoint.

The visual language follows the `speculative-web-visual-system` rules; tools remain independent backend packages rather than frontend prompt code.
