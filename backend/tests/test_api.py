"""API contract tests against a local HTTP fixture, not a Crawlab runtime test."""

import json
import threading
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi.testclient import TestClient
from pydantic import JsonValue, TypeAdapter

from app.application import create_app
from app.config import Settings

SPIDER_ID = "123456789012345678901234"
SCHEDULE_ID = "123456789012345678901235"
HEADERS = {"X-FlowHarbor-Request": "1"}


@dataclass
class Capture:
    requests: list[tuple[str, str, dict[str, str], dict[str, JsonValue]]] = field(default_factory=list)
    status: int = 200
    schedule_enabled: bool = True
    linked: int = 0
    malformed: bool = False
    result_rows: list[dict[str, JsonValue]] = field(default_factory=list)


@pytest.fixture
def upstream():
    capture = Capture()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object):
            pass

        def respond(self):
            path = urlsplit(self.path).path
            query = {key: values[0] for key, values in parse_qs(urlsplit(self.path).query).items()}
            payload = TypeAdapter(dict[str, JsonValue]).validate_json(
                self.rfile.read(int(self.headers.get("Content-Length", "0"))) or b"{}"
            )
            capture.requests.append((self.command, path, query, payload))
            if capture.status != 200:
                self.send_response(capture.status)
                self.end_headers()
                return
            if capture.malformed:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"<html>Not Crawlab</html>")
                return
            if path == "/api/login":
                self.send_json("upstream-jwt-value")
                return
            if self.headers.get("Authorization") != "upstream-jwt-value":
                self.send_response(401)
                self.end_headers()
                return
            if self.command == "DELETE":
                self.send_response(200)
                self.end_headers()
                return
            if self.command in {"POST", "PUT"}:
                self.send_json(payload)
                return
            if path == "/api/users/me":
                self.send_json({"_id": SPIDER_ID, "username": "admin", "role": "admin", "email": ""})
                return
            if path == f"/api/spiders/{SPIDER_ID}":
                self.send_json({"_id": SPIDER_ID, "col_id": SCHEDULE_ID, "type": "customized", "name": "demo"})
                return
            if path == f"/api/schedules/{SCHEDULE_ID}":
                self.send_json({"_id": SCHEDULE_ID, "enabled": capture.schedule_enabled, "entry_id": 42, "user_id": SPIDER_ID})
                return
            if path == f"/api/tasks/{SPIDER_ID}/data":
                self.send_json(capture.result_rows, len(capture.result_rows))
                return
            self.send_json(None, capture.linked)

        def send_json(self, data: JsonValue, total: int = 0):
            encoded = json.dumps({"status": "ok", "message": "success", "error": "", "data": data, "total": total}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        do_GET = respond
        do_POST = respond
        do_PUT = respond
        do_DELETE = respond

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield capture, f"http://127.0.0.1:{server.server_port}/api/"
    server.shutdown()
    server.server_close()
    thread.join()


@pytest.fixture
def client(upstream):
    with TestClient(create_app(Settings(crawlab_base_url=upstream[1], session_secret="test-session-secret-with-at-least-32-characters"))) as session:
        yield session


def sign_in(client: TestClient):
    response = client.post("/api/login", json={"username": "admin", "password": "valid-password"}, headers=HEADERS)
    assert response.status_code == 200
    return response


def test_signed_cookie_auth_and_logout(client):
    assert client.get("/api/projects").status_code == 401
    response = sign_in(client)
    assert response.json() == {"data": {"username": "admin"}}
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "SameSite=strict" in response.headers["set-cookie"]
    assert client.cookies["flowharbor_session"] != "upstream-jwt-value"
    assert client.get("/api/session").json()["data"]["username"] == "admin"
    assert client.post("/api/logout", headers=HEADERS).status_code == 200
    assert client.get("/api/session").status_code == 401


def test_tampered_cookie_is_rejected_before_engine(client, upstream):
    client.cookies.set("flowharbor_session", "forged-crawlab-token", path="/api")
    assert client.get("/api/session").status_code == 401
    assert not upstream[0].requests


def test_csrf_header_and_origin_are_required_for_browser_writes(client, upstream):
    payload = {"username": "admin", "password": "password"}
    assert client.post("/api/login", json=payload).status_code == 403
    assert client.post("/api/login", json=payload, headers={**HEADERS, "Origin": "https://evil.example"}).status_code == 403
    assert not upstream[0].requests
    assert client.post("/api/login", json=payload, headers={**HEADERS, "Origin": "http://localhost:8080"}).status_code == 200


@pytest.mark.parametrize("path", ["../outside.py", "/etc/passwd", "C:\\tmp\\main.py", "folder/../../main.py", "."])
def test_file_path_traversal_never_reaches_engine(client, upstream, path):
    sign_in(client)
    count = len(upstream[0].requests)
    response = client.post(f"/api/spiders/{SPIDER_ID}/files", json={"path": path, "content": "print('hello')"}, headers=HEADERS)
    assert response.status_code == 422
    assert len(upstream[0].requests) == count


def test_script_upload_maps_to_crawlab_file_save(client, upstream):
    sign_in(client)
    response = client.post(f"/api/spiders/{SPIDER_ID}/files", json={"path": "main.py", "content": "print('hello')"}, headers=HEADERS)
    assert response.status_code == 200
    assert upstream[0].requests[-1] == ("POST", f"/api/spiders/{SPIDER_ID}/files/save", {}, {"path": "main.py", "data": "print('hello')"})


@pytest.mark.parametrize("cron", ["* * *", "0 * * * * *", "60 * * * *", "*/0 * * * *", "* * * * 7", "* 5-2 * * *"])
def test_invalid_cron_does_not_create_schedule(client, upstream, cron):
    sign_in(client)
    count = len(upstream[0].requests)
    response = client.post("/api/schedules", json={"name": "demo", "spider_id": SPIDER_ID, "cron": cron}, headers=HEADERS)
    assert response.status_code == 422
    assert len(upstream[0].requests) == count


def test_schedule_update_preserves_live_entry_and_user(client, upstream):
    sign_in(client)
    response = client.put(f"/api/schedules/{SCHEDULE_ID}", json={"name": "changed", "spider_id": SPIDER_ID, "cron": "*/2 * * * *"}, headers=HEADERS)
    assert response.status_code == 200
    payload = upstream[0].requests[-1][3]
    assert payload["entry_id"] == 42
    assert payload["user_id"] == SPIDER_ID
    assert payload["_id"] == SCHEDULE_ID


def test_disabling_via_update_removes_cron_before_save(client, upstream):
    sign_in(client)
    response = client.put(f"/api/schedules/{SCHEDULE_ID}", json={"name": "paused", "spider_id": SPIDER_ID, "enabled": False}, headers=HEADERS)
    assert response.status_code == 200
    assert upstream[0].requests[-2][1] == f"/api/schedules/{SCHEDULE_ID}/disable"
    assert upstream[0].requests[-1][3]["entry_id"] == -1


def test_repeated_enable_does_not_duplicate_cron(client, upstream):
    sign_in(client)
    assert client.post(f"/api/schedules/{SCHEDULE_ID}/enable", headers=HEADERS).status_code == 200
    assert upstream[0].requests[-1][0] == "GET"


def test_spider_create_generates_collection_and_update_preserves_id(client, upstream):
    sign_in(client)
    assert client.post("/api/spiders", json={"name": "example"}, headers=HEADERS).status_code == 200
    assert str(upstream[0].requests[-1][3]["col_name"]).startswith("fh_")
    assert client.put(f"/api/spiders/{SPIDER_ID}", json={"name": "changed"}, headers=HEADERS).status_code == 200
    assert upstream[0].requests[-1][3]["col_id"] == SCHEDULE_ID


def test_pagination_and_status_filters_map_to_engine(client, upstream):
    sign_in(client)
    response = client.get(f"/api/tasks?page=2&size=10&status=running&spider_id={SPIDER_ID}")
    assert response.json() == {"data": [], "total": 0}
    query = upstream[0].requests[-1][2]
    assert query["page"] == "2"
    assert query["size"] == "10"
    assert json.loads(query["conditions"]) == [
        {"key": "status", "op": "eq", "value": "running"},
        {"key": "spider_id", "op": "eq", "value": SPIDER_ID},
    ]
    assert client.get("/api/tasks?size=201").status_code == 422


def test_selected_nodes_requires_a_node(client, upstream):
    sign_in(client)
    count = len(upstream[0].requests)
    assert client.post(f"/api/spiders/{SPIDER_ID}/run", json={"mode": "selected-nodes"}, headers=HEADERS).status_code == 422
    assert len(upstream[0].requests) == count


def test_logs_and_results_use_correct_upstream_paths(client, upstream):
    sign_in(client)
    assert client.get(f"/api/tasks/{SPIDER_ID}/logs").json() == {"data": [], "total": 0}
    assert upstream[0].requests[-1][1].endswith("/logs")
    assert client.get(f"/api/tasks/{SPIDER_ID}/results").status_code == 200
    assert upstream[0].requests[-1][1].endswith("/data")


def test_delete_schedule_accepts_empty_upstream_200(client):
    sign_in(client)
    assert client.delete(f"/api/schedules/{SCHEDULE_ID}", headers=HEADERS).json() == {"data": None}


def test_project_delete_blocks_linked_spiders(client, upstream):
    sign_in(client)
    upstream[0].linked = 1
    assert client.delete(f"/api/projects/{SPIDER_ID}", headers=HEADERS).status_code == 409
    assert upstream[0].requests[-1][0] == "GET"


def test_engine_failure_and_malformed_response_are_visible(client, upstream):
    sign_in(client)
    upstream[0].status = 500
    assert client.get("/api/projects").status_code == 502
    upstream[0].status = 401
    assert client.get("/api/session").status_code == 401
    upstream[0].status = 200
    upstream[0].malformed = True
    assert client.get("/api/projects").status_code == 502


def test_health_does_not_claim_engine_readiness(client, upstream):
    upstream[0].status = 500
    assert client.get("/api/health").json() == {"status": "ok", "version": "0.1.0"}
    assert not upstream[0].requests


def test_empty_spider_directory_returns_empty_file_list(client, upstream):
    sign_in(client)
    assert client.get(f"/api/spiders/{SPIDER_ID}/files").json() == {"data": []}
    assert upstream[0].requests[-1][1:3] == (f"/api/spiders/{SPIDER_ID}/files/list", {"path": "/"})


@pytest.mark.parametrize("resource", ["projects", "spiders", "schedules"])
def test_name_search_treats_regex_characters_as_literal_text(client, upstream, resource):
    sign_in(client)
    response = client.get(f"/api/{resource}", params={"keyword": "[daily].*"})
    assert response.status_code == 200
    assert json.loads(upstream[0].requests[-1][2]["conditions"]) == [
        {"key": "name", "op": "c", "value": r"\[daily\]\.\*"},
    ]


def test_user_result_fields_are_not_rewritten(client, upstream):
    sign_in(client)
    upstream[0].result_rows = [{"sku": "FH-001", "node_ids": None}]
    assert client.get(f"/api/tasks/{SPIDER_ID}/results").json() == {
        "data": [{"sku": "FH-001", "node_ids": None}], "total": 1,
    }
