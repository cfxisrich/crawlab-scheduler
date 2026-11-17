import json
from dataclasses import dataclass
from typing import Literal

import httpx
from fastapi import HTTPException
from pydantic import BaseModel, JsonValue, ValidationError


class Envelope(BaseModel):
    status: str
    message: str
    data: JsonValue = None
    error: str = ""
    total: int = 0


@dataclass
class Page:
    data: list[JsonValue]
    total: int


class Engine:
    def __init__(self, base_url: str):
        self.http = httpx.AsyncClient(base_url=base_url.rstrip("/") + "/", timeout=30, follow_redirects=False)

    async def request(
        self,
        method: Literal["GET", "POST", "PUT", "DELETE"],
        path: str,
        token: str = "",
        payload: dict[str, JsonValue] | None = None,
        params: dict[str, str | int] | None = None,
    ) -> Envelope:
        try:
            response = await self.http.request(method, path, headers={"Authorization": token}, json=payload, params=params)
        except httpx.TimeoutException as error:
            raise HTTPException(504, "Crawlab 响应超时，请检查执行引擎") from error
        except httpx.RequestError as error:
            raise HTTPException(502, "无法连接 Crawlab，请检查部署和网络") from error
        if response.status_code == 401:
            raise HTTPException(401, "登录已失效或账号密码错误")
        if response.status_code >= 400:
            raise HTTPException(response.status_code if response.status_code < 500 else 502, "Crawlab 拒绝了操作，请检查参数及引擎日志")
        # Crawlab 0.6.3 schedule DELETE returns an empty 200 response.
        if method == "DELETE" and not response.content:
            return Envelope(status="ok", message="success")
        try:
            envelope = Envelope.model_validate_json(response.content)
        except ValidationError as error:
            raise HTTPException(502, "Crawlab 返回了无法解析的响应") from error
        if envelope.error:
            raise HTTPException(502, "Crawlab 执行失败，请查看引擎日志")
        return envelope

    async def object(self, path: str, token: str) -> dict[str, JsonValue]:
        response = await self.request("GET", path, token)
        if not isinstance(response.data, dict):
            raise HTTPException(502, "Crawlab 资源响应格式错误")
        return response.data

    async def listing(
        self, path: str, token: str, page: int = 1, size: int = 20,
        conditions: list[dict[str, JsonValue]] | None = None,
    ) -> Page:
        response = await self.request("GET", path, token, params={
            "page": page, "size": size, "stats": "true",
            "conditions": json.dumps(conditions or []),
            "sort": '[{"key":"_id","d":"desc"}]',
        })
        if response.data is None:
            return Page(data=[], total=response.total)
        if not isinstance(response.data, list):
            raise HTTPException(502, "Crawlab 列表响应格式错误")
        return Page(data=response.data, total=response.total)
