import os
import time
import uuid
from contextlib import ExitStack
from pathlib import Path

import httpx
import pytest


pytestmark = pytest.mark.skipif(
    os.getenv("FLOWHARBOR_INTEGRATION") != "1",
    reason="设置 FLOWHARBOR_INTEGRATION=1 才连接真实引擎",
)


def request(client, method, path, payload=None):
    response = client.request(method, f"/api{path}", json=payload)
    response.raise_for_status()
    return response.json()


def wait_finished(client, task_id):
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        task = request(client, "GET", f"/tasks/{task_id}")["data"]
        if task["status"] == "finished":
            return task
        assert task["status"] in {"pending", "running"}, task
        time.sleep(2)
    pytest.fail(f"任务 {task_id} 在 180 秒内未完成")


def test_live_catalog_and_cron():
    with httpx.Client(
        base_url=os.getenv("FLOWHARBOR_TEST_URL", "http://localhost:8080"),
        headers={"X-FlowHarbor-Request": "1"},
        timeout=30,
        trust_env=False,
    ) as client, ExitStack() as cleanup:
        request(client, "POST", "/login", {
            "username": os.environ["FLOWHARBOR_TEST_USERNAME"],
            "password": os.environ["FLOWHARBOR_TEST_PASSWORD"],
        })
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            nodes = request(client, "GET", "/nodes?size=100")["data"]
            workers = [node for node in nodes if node["active"] and not node["is_master"]]
            if workers:
                break
            time.sleep(2)
        assert workers, "90 秒内没有 Worker 注册上线"
        project = request(client, "POST", "/projects", {
            "name": f"integration-{uuid.uuid4().hex[:10]}",
            "description": "真实引擎验收，测试结束自动删除",
        })["data"]
        cleanup.callback(request, client, "DELETE", f"/projects/{project['_id']}")
        spider = request(client, "POST", "/spiders", {
            "name": "fixture-catalog",
            "project_id": project["_id"],
            "cmd": "python main.py --url http://fixture/",
            "mode": "selected-nodes",
            "node_ids": [workers[0]["_id"]],
        })["data"]
        cleanup.callback(request, client, "DELETE", f"/spiders/{spider['_id']}")
        assert spider["col_id"] != "000000000000000000000000"
        source = (Path(__file__).resolve().parents[2] / "examples" / "catalog" / "main.py").read_text(encoding="utf-8")
        request(client, "POST", f"/spiders/{spider['_id']}/files", {
            "path": "main.py", "content": source,
        })
        assert request(client, "GET", f"/spiders/{spider['_id']}/file?path=main.py")["data"] == source
        execution = {
            "cmd": spider["cmd"], "param": "", "priority": 0,
            "mode": "selected-nodes", "node_ids": [workers[0]["_id"]],
        }
        task_ids = request(client, "POST", f"/spiders/{spider['_id']}/run", execution)["data"]
        assert len(task_ids) == 1
        task = wait_finished(client, task_ids[0])
        assert task["node_id"] == workers[0]["_id"]
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            results = request(client, "GET", f"/tasks/{task_ids[0]}/results")
            logs = request(client, "GET", f"/tasks/{task_ids[0]}/logs?size=200")
            if results["total"] == 3 and any("FLOWHARBOR_CATALOG_SAVED count=3" in row["msg"] for row in logs["data"]):
                break
            time.sleep(2)
        assert results["total"] == 3, results
        assert {row["sku"] for row in results["data"]} == {"FH-001", "FH-002", "FH-003"}
        assert any("FLOWHARBOR_CATALOG_SAVED count=3" in row["msg"] for row in logs["data"]), logs
        schedule = request(client, "POST", "/schedules", {
            **execution, "name": "integration-every-minute", "description": "真实 Cron 验收",
            "spider_id": spider["_id"], "cron": "* * * * *", "enabled": True,
        })["data"]
        cleanup.callback(request, client, "DELETE", f"/schedules/{schedule['_id']}")
        request(client, "PUT", f"/schedules/{schedule['_id']}", {
            **execution, "name": "integration-updated", "description": "更新启用中的计划",
            "spider_id": spider["_id"], "cron": "* * * * *", "enabled": True,
        })
        request(client, "POST", f"/schedules/{schedule['_id']}/enable")
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            scheduled = request(client, "GET", f"/tasks?schedule_id={schedule['_id']}&size=100")
            if scheduled["total"]:
                break
            time.sleep(2)
        assert scheduled["total"] > 0, "90 秒内没有产生定时任务"
        request(client, "POST", f"/schedules/{schedule['_id']}/disable")
        for scheduled_task in scheduled["data"]:
            wait_finished(client, scheduled_task["_id"])
        schedules = request(client, "GET", f"/schedules?spider_id={spider['_id']}")["data"]
        assert next(item for item in schedules if item["_id"] == schedule["_id"])["enabled"] is False
        before = request(client, "GET", f"/tasks?schedule_id={schedule['_id']}")["total"]
        deadline = time.monotonic() + 70
        while time.monotonic() < deadline:
            time.sleep(2)
            assert request(client, "GET", f"/tasks?schedule_id={schedule['_id']}")["total"] == before
