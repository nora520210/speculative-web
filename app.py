from __future__ import annotations

import json
import mimetypes
import os
import shutil
import sys
import uuid
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from server.config import (
    GENERATED_IMAGE_DIR,
    MAX_JSON_BODY_BYTES,
    MAX_UPLOAD_BYTES,
    MAX_USER_API_KEY_CHARS,
    UPLOAD_DIR,
    storage_mode,
    user_api_key_required,
)
from server.documents import inspect_document
from server.graph_store import (
    add_edge,
    add_node,
    create_project,
    delete_edge,
    delete_node,
    delete_project,
    ensure_store,
    get_project,
    read_canvas,
    read_projects,
    recommend_output_for_modify,
    run_modify,
    update_node,
    update_project,
)
from server.model_service import model_environment_status
from server.modifier_registry import list_output_types, public_modifier_tools
from server.rendering import render_document


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"


def ensure_data() -> None:
    ensure_store()
    UPLOAD_DIR.mkdir(exist_ok=True)


class AppHandler(SimpleHTTPRequestHandler):
    server_version = "SpeculativeWeb/0.1"

    def translate_path(self, path: str) -> str:
        parsed = urlparse(path)
        clean = parsed.path.lstrip("/")
        if clean.startswith("static/"):
            candidate = (ROOT / clean).resolve()
            static_root = STATIC_DIR.resolve()
            if candidate == static_root or static_root in candidate.parents:
                return str(candidate)
            return str(STATIC_DIR / "__not_found__")
        if clean.startswith("generated/"):
            candidate = (GENERATED_IMAGE_DIR / clean.removeprefix("generated/")).resolve()
            generated_root = GENERATED_IMAGE_DIR.resolve()
            if candidate == generated_root or generated_root in candidate.parents:
                return str(candidate)
            return str(GENERATED_IMAGE_DIR / "__not_found__")
        return str(STATIC_DIR / "index.html")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self.send_json(
                {
                    "ok": True,
                    "app": "speculative-web",
                    "python": sys.version.split()[0],
                    "storage_mode": storage_mode(),
                    "api": {
                        "projects": "/api/projects",
                        "canvas": "/api/projects/{project_id}/canvas",
                        "tools": "/api/modifier-tools",
                        "model": "/api/model/status",
                    },
                }
            )
            return

        if parsed.path == "/api/projects":
            projects = sorted(
                read_projects(),
                key=lambda item: item.get("updated_at", ""),
                reverse=True,
            )
            self.send_json({"projects": projects})
            return

        if parsed.path == "/api/modifier-tools":
            self.send_json({"tools": public_modifier_tools(), "output_types": list_output_types()})
            return

        if parsed.path == "/api/model/status":
            self.send_json({"model": model_environment_status()})
            return

        route = self.match_project_route(parsed.path)
        if route and len(route) == 2 and route[1] == "canvas":
            project_id = route[0]
            if not get_project(project_id):
                self.send_json({"error": "Project not found."}, status=HTTPStatus.NOT_FOUND)
                return
            self.send_json({"canvas": read_canvas(project_id)})
            return

        if route and len(route) == 4 and route[1] == "nodes" and route[3] == "output-recommendation":
            project_id = route[0]
            node_id = route[2]
            canvas = read_canvas(project_id)
            node = next((item for item in canvas.get("nodes", []) if item.get("id") == node_id), None)
            if not node:
                self.send_json({"error": "Node not found."}, status=HTTPStatus.NOT_FOUND)
                return
            if node.get("type") != "modify":
                self.send_json({"error": "Only Modify nodes expose output recommendations."}, status=HTTPStatus.BAD_REQUEST)
                return
            self.send_json({"recommendation": recommend_output_for_modify(node)})
            return

        super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if not self.headers.get("Content-Type", "").startswith("multipart/form-data"):
            if self.request_too_large(MAX_JSON_BODY_BYTES):
                return
        if parsed.path == "/api/projects":
            payload = self.read_json_body()
            title = str(payload.get("title") or "Untitled Canvas").strip()
            project = create_project(title)
            self.send_json({"project": project}, status=HTTPStatus.CREATED)
            return

        route = self.match_project_route(parsed.path)
        if route and len(route) >= 2:
            project_id = route[0]
            action = route[1:]
            if not get_project(project_id):
                self.send_json({"error": "Project not found."}, status=HTTPStatus.NOT_FOUND)
                return

            if action == ["nodes"]:
                payload = self.read_json_body()
                try:
                    node = add_node(project_id, payload)
                except ValueError as exc:
                    self.send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                    return
                self.send_json({"node": node}, status=HTTPStatus.CREATED)
                return

            if action == ["edges"]:
                payload = self.read_json_body()
                try:
                    edge = add_edge(project_id, payload)
                except (KeyError, ValueError) as exc:
                    self.send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                    return
                self.send_json({"edge": edge}, status=HTTPStatus.CREATED)
                return

            if len(action) == 3 and action[0] == "nodes" and action[2] == "run":
                node_id = action[1]
                api_key = self.user_api_key()
                if user_api_key_required() and not api_key:
                    self.send_json(
                        {"error": "Enter an API key in this browser tab before running a Modify node."},
                        status=HTTPStatus.UNAUTHORIZED,
                    )
                    return
                try:
                    result = run_modify(project_id, node_id, api_key=api_key or None)
                except (KeyError, ValueError) as exc:
                    self.send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                    return
                self.send_json(result, status=HTTPStatus.CREATED)
                return

        if parsed.path == "/api/documents/inspect":
            self.handle_document_inspect()
            return

        if parsed.path == "/api/documents/render":
            self.handle_document_render()
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")

    def do_PATCH(self) -> None:
        parsed = urlparse(self.path)
        if self.request_too_large(MAX_JSON_BODY_BYTES):
            return
        route = self.match_project_route(parsed.path)
        if route and len(route) == 1:
            project_id = route[0]
            try:
                project = update_project(project_id, self.read_json_body())
            except KeyError as exc:
                self.send_json({"error": str(exc)}, status=HTTPStatus.NOT_FOUND)
                return
            except ValueError as exc:
                self.send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                return
            self.send_json({"project": project})
            return
        if route and len(route) == 3 and route[1] == "nodes":
            project_id, _, node_id = route
            if not get_project(project_id):
                self.send_json({"error": "Project not found."}, status=HTTPStatus.NOT_FOUND)
                return
            try:
                node = update_node(project_id, node_id, self.read_json_body())
            except KeyError as exc:
                self.send_json({"error": str(exc)}, status=HTTPStatus.NOT_FOUND)
                return
            self.send_json({"node": node})
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        route = self.match_project_route(parsed.path)
        if route and len(route) == 1:
            project_id = route[0]
            try:
                result = delete_project(project_id)
            except KeyError as exc:
                self.send_json({"error": str(exc)}, status=HTTPStatus.NOT_FOUND)
                return
            self.send_json(result)
            return
        if route and len(route) == 3 and route[1] == "edges":
            project_id, _, edge_id = route
            if not get_project(project_id):
                self.send_json({"error": "Project not found."}, status=HTTPStatus.NOT_FOUND)
                return
            try:
                result = delete_edge(project_id, edge_id)
            except KeyError as exc:
                self.send_json({"error": str(exc)}, status=HTTPStatus.NOT_FOUND)
                return
            self.send_json(result)
            return
        if route and len(route) == 3 and route[1] == "nodes":
            project_id, _, node_id = route
            if not get_project(project_id):
                self.send_json({"error": "Project not found."}, status=HTTPStatus.NOT_FOUND)
                return
            try:
                result = delete_node(project_id, node_id)
            except KeyError as exc:
                self.send_json({"error": str(exc)}, status=HTTPStatus.NOT_FOUND)
                return
            self.send_json(result)
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")

    def handle_document_inspect(self) -> None:
        content_type = self.headers.get("Content-Type", "")
        if not content_type.startswith("multipart/form-data"):
            self.send_json(
                {"error": "Expected multipart/form-data with a file field."},
                status=HTTPStatus.BAD_REQUEST,
            )
            return
        if self.request_too_large(MAX_UPLOAD_BYTES):
            return

        import cgi

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": content_type,
            },
        )
        field = form["file"] if "file" in form else None
        if field is None or not getattr(field, "filename", ""):
            self.send_json(
                {"error": "Missing uploaded file."},
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        safe_name = Path(field.filename).name
        upload_path = UPLOAD_DIR / f"{uuid.uuid4().hex[:10]}-{safe_name}"
        with upload_path.open("wb") as out:
            shutil.copyfileobj(field.file, out)

        try:
            result = inspect_document(upload_path)
        except Exception as exc:  # keep API errors explainable in the prototype
            self.send_json(
                {"error": str(exc), "filename": safe_name},
                status=HTTPStatus.UNPROCESSABLE_ENTITY,
            )
            return

        self.send_json({"document": result})

    def handle_document_render(self) -> None:
        content_type = self.headers.get("Content-Type", "")
        if not content_type.startswith("multipart/form-data"):
            self.send_json(
                {"error": "Expected multipart/form-data with a file field."},
                status=HTTPStatus.BAD_REQUEST,
            )
            return
        if self.request_too_large(MAX_UPLOAD_BYTES):
            return

        import cgi

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": content_type,
            },
        )
        field = form["file"] if "file" in form else None
        if field is None or not getattr(field, "filename", ""):
            self.send_json(
                {"error": "Missing uploaded file."},
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        safe_name = Path(field.filename).name
        upload_path = UPLOAD_DIR / f"{uuid.uuid4().hex[:10]}-{safe_name}"
        with upload_path.open("wb") as out:
            shutil.copyfileobj(field.file, out)

        try:
            result = render_document(upload_path)
        except Exception as exc:
            self.send_json(
                {"error": str(exc), "filename": safe_name},
                status=HTTPStatus.UNPROCESSABLE_ENTITY,
            )
            return

        self.send_json({"render": result})

    def read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def request_too_large(self, limit: int) -> bool:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= limit:
            return False
        self.send_json(
            {"error": f"Request body exceeds {limit} bytes."},
            status=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
        )
        return True

    def match_project_route(self, path: str) -> list[str] | None:
        parts = [part for part in path.strip("/").split("/") if part]
        if len(parts) >= 3 and parts[0] == "api" and parts[1] == "projects":
            return parts[2:]
        return None

    def user_api_key(self) -> str:
        key = self.headers.get("X-Speculative-Web-Api-Key", "").strip()
        if len(key) > MAX_USER_API_KEY_CHARS:
            return ""
        return key

    def send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; connect-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline'; script-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'",
        )
        if self.headers.get("X-Forwarded-Proto") == "https":
            self.send_header("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        if self.path.startswith("/static/") or self.path.startswith("/generated/"):
            ctype = mimetypes.guess_type(self.path)[0]
            if ctype:
                self.send_header("Content-Type", ctype)
        super().end_headers()


def main() -> None:
    ensure_data()
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "127.0.0.1")
    server = ThreadingHTTPServer((host, port), AppHandler)
    print(f"Speculative Web running at http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
