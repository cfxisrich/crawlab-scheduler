import asyncio
import re
from contextlib import asynccontextmanager
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import Cookie, Depends, FastAPI, HTTPException, Query, Request, Response
from itsdangerous import BadSignature, TimestampSigner
from pydantic import AfterValidator, JsonValue
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import JSONResponse

from .config import Settings
from .engine import Engine
from .schemas import Login, ObjectId, Project, Run, Schedule, ScriptFile, Spider, TaskStatus, relative_file_path

PageNumber = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=200)]
Keyword = Annotated[str, Query(max_length=120)]
FilePath = Annotated[str, AfterValidator(relative_file_path)]


def create_app(settings: Settings) -> FastAPI:
    engine = Engine(str(settings.crawlab_base_url))
    signer = TimestampSigner(settings.session_secret, salt="flowharbor.session.v1")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        await engine.http.aclose()

    app = FastAPI(title="FlowHarbor API", version="0.1.0", lifespan=lifespan)

    @app.middleware("http")
    async def same_origin(request: Request, call_next: RequestResponseEndpoint):
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            if request.headers.get("X-FlowHarbor-Request") != "1":
                return JSONResponse({"detail": "缺少请求校验头"}, status_code=403)
            if "origin" in request.headers and request.headers["origin"] != settings.public_origin:
                return JSONResponse({"detail": "请求来源不匹配"}, status_code=403)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    def authenticate(flowharbor_session: Annotated[str | None, Cookie()] = None) -> str:
        if flowharbor_session is None:
            raise HTTPException(401, "请先登录")
        try:
            return signer.unsign(flowharbor_session, max_age=28800).decode("utf-8")
        except BadSignature as error:
            raise HTTPException(401, "登录已失效，请重新登录") from error

    Session = Annotated[str, Depends(authenticate)]

    @app.get("/api/health")
    def health():
        return {"status": "ok", "version": "0.1.0"}

    @app.post("/api/login")
    async def login(payload: Login, response: Response):
        result = await engine.request("POST", "login", payload=payload.model_dump())
        if not isinstance(result.data, str) or not result.data:
            raise HTTPException(502, "Crawlab 登录响应格式错误")
        response.set_cookie("flowharbor_session", signer.sign(result.data).decode("utf-8"),
                            max_age=28800, httponly=True, secure=settings.cookie_secure,
                            samesite="strict", path="/api")
        return {"data": {"username": payload.username}}

    @app.post("/api/logout")
    def logout(response: Response):
        response.delete_cookie("flowharbor_session", path="/api", secure=settings.cookie_secure,
                               httponly=True, samesite="strict")
        return {"data": None}

    @app.get("/api/session")
    async def session(token: Session):
        return {"data": (await engine.request("GET", "users/me", token)).data}

    @app.get("/api/overview")
    async def overview(token: Session):
        projects, spiders, tasks, running, failed, schedules, nodes, online = await asyncio.gather(
            engine.listing("projects", token, size=1),
            engine.listing("spiders", token, size=1),
            engine.listing("tasks", token, size=8),
            engine.listing("tasks", token, size=1, conditions=[{"key": "status", "op": "eq", "value": "running"}]),
            engine.listing("tasks", token, size=1, conditions=[{"key": "status", "op": "in", "value": ["error", "abnormal"]}]),
            engine.listing("schedules", token, size=1),
            engine.listing("nodes", token, size=1),
            engine.listing("nodes", token, size=1, conditions=[{"key": "active", "op": "eq", "value": True}]),
        )
        return {"data": {
            "projects": projects.total, "spiders": spiders.total, "tasks": tasks.total,
            "running": running.total, "failed": failed.total, "schedules": schedules.total,
            "nodes": nodes.total, "online_nodes": online.total, "recent_tasks": tasks.data,
        }}

    @app.get("/api/projects")
    async def projects(token: Session, page: PageNumber = 1, size: PageSize = 20, keyword: Keyword = ""):
        return await engine.listing("projects", token, page, size,
                                    [{"key": "name", "op": "c", "value": re.escape(keyword)}] if keyword else [])

    @app.post("/api/projects")
    async def create_project(payload: Project, token: Session):
        return {"data": (await engine.request("POST", "projects", token, payload.model_dump())).data}

    @app.put("/api/projects/{id}")
    async def update_project(id: ObjectId, payload: Project, token: Session):
        return {"data": (await engine.request("PUT", f"projects/{id}", token, {**payload.model_dump(), "_id": id})).data}

    @app.delete("/api/projects/{id}")
    async def delete_project(id: ObjectId, token: Session):
        linked = await engine.listing("spiders", token, size=1, conditions=[{"key": "project_id", "op": "eq", "value": id}])
        if linked.total:
            raise HTTPException(409, "项目下仍有任务，请先移动或删除任务")
        await engine.request("DELETE", f"projects/{id}", token)
        return {"data": None}

    @app.get("/api/spiders")
    async def spiders(token: Session, page: PageNumber = 1, size: PageSize = 20,
                      keyword: Keyword = "", project_id: ObjectId | None = None):
        conditions: list[dict[str, JsonValue]] = []
        if keyword:
            conditions.append({"key": "name", "op": "c", "value": re.escape(keyword)})
        if project_id:
            conditions.append({"key": "project_id", "op": "eq", "value": project_id})
        return await engine.listing("spiders", token, page, size, conditions)

    @app.get("/api/spiders/{id}")
    async def spider(id: ObjectId, token: Session):
        return {"data": (await engine.request("GET", f"spiders/{id}", token)).data}

    @app.post("/api/spiders")
    async def create_spider(payload: Spider, token: Session):
        return {"data": (await engine.request("POST", "spiders", token, {
            **payload.model_dump(), "type": "customized", "col_name": payload.col_name or f"fh_{uuid4().hex}",
        })).data}

    @app.put("/api/spiders/{id}")
    async def update_spider(id: ObjectId, payload: Spider, token: Session):
        existing = await engine.object(f"spiders/{id}", token)
        return {"data": (await engine.request("PUT", f"spiders/{id}", token, {
            **existing, **payload.model_dump(), "_id": id,
        })).data}

    @app.delete("/api/spiders/{id}")
    async def delete_spider(id: ObjectId, token: Session):
        schedules, tasks = await asyncio.gather(
            engine.listing("schedules", token, size=1, conditions=[{"key": "spider_id", "op": "eq", "value": id}]),
            engine.listing("tasks", token, size=1, conditions=[
                {"key": "spider_id", "op": "eq", "value": id},
                {"key": "status", "op": "in", "value": ["pending", "running"]},
            ]),
        )
        if schedules.total or tasks.total:
            raise HTTPException(409, "任务仍有关联计划或未结束的执行，请先处理后再删除")
        await engine.request("DELETE", f"spiders/{id}", token)
        return {"data": None}

    @app.post("/api/spiders/{id}/files")
    async def save_file(id: ObjectId, payload: ScriptFile, token: Session):
        await engine.request("POST", f"spiders/{id}/files/save", token, {"path": payload.path, "data": payload.content})
        return {"data": None}

    @app.get("/api/spiders/{id}/files")
    async def files(id: ObjectId, token: Session):
        result = await engine.request("GET", f"spiders/{id}/files/list", token, params={"path": "/"})
        return {"data": [] if result.data is None else result.data}

    @app.get("/api/spiders/{id}/file")
    async def file(id: ObjectId, path: FilePath, token: Session):
        return {"data": (await engine.request("GET", f"spiders/{id}/files/get", token, params={"path": path})).data}

    @app.post("/api/spiders/{id}/run")
    async def run(id: ObjectId, payload: Run, token: Session):
        return {"data": (await engine.request("POST", f"spiders/{id}/run", token, payload.model_dump())).data}

    @app.get("/api/tasks")
    async def tasks(token: Session, page: PageNumber = 1, size: PageSize = 20, status: TaskStatus | None = None,
                    spider_id: ObjectId | None = None, schedule_id: ObjectId | None = None):
        return await engine.listing("tasks", token, page, size, [
            {"key": key, "op": "eq", "value": value}
            for key, value in [("status", status), ("spider_id", spider_id), ("schedule_id", schedule_id)] if value
        ])

    @app.get("/api/tasks/{id}")
    async def task(id: ObjectId, token: Session):
        return {"data": (await engine.request("GET", f"tasks/{id}", token)).data}

    @app.post("/api/tasks/{id}/{action}")
    async def task_action(id: ObjectId, action: Literal["cancel", "restart"], token: Session):
        return {"data": (await engine.request("POST", f"tasks/{id}/{action}", token, {})).data}

    @app.get("/api/tasks/{id}/logs")
    async def logs(id: ObjectId, token: Session, page: PageNumber = 1, size: PageSize = 200):
        return await engine.listing(f"tasks/{id}/logs", token, page, size)

    @app.get("/api/tasks/{id}/results")
    async def results(id: ObjectId, token: Session, page: PageNumber = 1, size: PageSize = 20):
        return await engine.listing(f"tasks/{id}/data", token, page, size)

    @app.get("/api/schedules")
    async def schedules(token: Session, page: PageNumber = 1, size: PageSize = 20,
                        keyword: Keyword = "", spider_id: ObjectId | None = None):
        conditions: list[dict[str, JsonValue]] = []
        if keyword:
            conditions.append({"key": "name", "op": "c", "value": re.escape(keyword)})
        if spider_id:
            conditions.append({"key": "spider_id", "op": "eq", "value": spider_id})
        return await engine.listing("schedules", token, page, size, conditions)

    @app.post("/api/schedules")
    async def create_schedule(payload: Schedule, token: Session):
        return {"data": (await engine.request("POST", "schedules", token, payload.model_dump())).data}

    @app.put("/api/schedules/{id}")
    async def update_schedule(id: ObjectId, payload: Schedule, token: Session):
        existing = await engine.object(f"schedules/{id}", token)
        if existing["enabled"] and not payload.enabled:
            await engine.request("POST", f"schedules/{id}/disable", token, {})
            existing["entry_id"] = -1
        return {"data": (await engine.request("PUT", f"schedules/{id}", token, {
            **existing, **payload.model_dump(), "_id": id,
        })).data}

    @app.post("/api/schedules/{id}/{action}")
    async def schedule_action(id: ObjectId, action: Literal["enable", "disable"], token: Session):
        existing = await engine.object(f"schedules/{id}", token)
        if existing["enabled"] == (action == "enable"):
            return {"data": None}
        await engine.request("POST", f"schedules/{id}/{action}", token, {})
        return {"data": None}

    @app.delete("/api/schedules/{id}")
    async def delete_schedule(id: ObjectId, token: Session):
        await engine.request("DELETE", f"schedules/{id}", token)
        return {"data": None}

    @app.get("/api/nodes")
    async def nodes(token: Session, page: PageNumber = 1, size: PageSize = 100):
        return await engine.listing("nodes", token, page, size)

    return app
