# Speculative Web

Node-based speculative-design workspace for scientific and engineering research teams. Researchers add feasible research directions or materials; the Modify node owns tool selection, response structure, language inference, and image constraints.

## Local Run

```bash
python3 -m pip install -r requirements.txt
PORT=8002 python3 app.py
```

Open `http://127.0.0.1:8002`.

Copy `.env.example` to `.env` and add `OPENAI_API_KEY` only for live model runs. The key remains server-side.

## Interface Language

The compact `中文` / `EN` control in the top menu switches interface language and is saved locally in the browser. It intentionally does not translate research inputs, existing canvas titles, tool package theory, or generated content.

## Vercel Deployment

This repository is prepared for Vercel's Python runtime:

1. Import the GitHub repository in Vercel.
2. Vercel detects `vercel.json`; no build command is required.
3. In **Project Settings -> Environment Variables**, set:
   - `OPENAI_API_KEY` as a secret
   - `OPENAI_IMAGE_MODEL=gpt-image-2`
   - `SPEC_WEB_ENABLE_OPENAI_RUNS=1`
   - optionally `OPENAI_MODEL` for a fixed text model
4. Deploy and test `/api/health`.

The Vercel runtime uses `/tmp/speculative-web`, so canvases, uploaded documents, and generated image files are **ephemeral** there. The deployed site works within a warm runtime, but it must be connected to a durable database and object store before treating saved canvases as persistent production data. Do not add `OPENAI_API_KEY` to source files or browser-side code. Until authentication and usage controls are added, enable Vercel Deployment Protection or restrict site access to your team; otherwise an unauthenticated public Run endpoint could consume the model budget.

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
