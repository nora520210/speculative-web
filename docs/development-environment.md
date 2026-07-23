# Development Environment

This project starts as a lightweight Python + HTML system to avoid early dependency drag.

## Included Tools

- Python standard-library HTTP server in `app.py`.
- Static frontend in `static/`.
- PDF text extraction through `pdfplumber`.
- DOCX text extraction through `python-docx`.
- PDF rendering through bundled `pdftoppm`.
- DOCX rendering through bundled headless LibreOffice, then `pdftoppm`.
- Visual token check to guard the black-and-white interface direction.
- VS Code settings, launch config, tasks, and extension recommendations.
- Smoke test for server health and project API.

## Commands

```bash
make doctor
make test
make visual
make dev
```

Render a document:

```bash
make inspect FILE=/path/to/file.pdf
make render FILE=/path/to/file.pdf
make render FILE=/path/to/file.docx
```

## Notes

- Keep `OPENAI_API_KEY` in `.env` or shell environment only. Do not expose it to frontend code.
- Easiest API key setup: copy `.env.example` to `.env`, set `OPENAI_API_KEY=...`, then restart the server. You only enter the key once for the local project.
- Modify tool constraints can be edited through `data/tool_registry.json`; use `data/tool_registry.example.json` as the template.
- Workflow definitions are backend manifests in `workflow_definitions/`; they compose
  existing nodes, scopes, sessions, and operations rather than adding a separate chat
  or canvas runtime.
- Future graphical tool cards belong to the relevant `tool_packages/*/manifest.json`
  through the optional `presentation` contract. Keep any card asset package-relative;
  do not place tool-specific theory or execution rules in frontend code.
- `7.22SPEC/` is external reference material and is Git-ignored. Do not import from,
  run, or stage it when developing this system.
- The current server is intentionally minimal. Move to FastAPI or Flask only when routing, auth, async jobs, or OpenAI orchestration justify the dependency.
- The visual system is stored as the `speculative-web-visual-system` Codex skill.
