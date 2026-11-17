import re
from pathlib import PurePosixPath
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

ObjectId = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{24}$")]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
RunMode = Literal["random", "selected-nodes", "all-nodes"]
TaskStatus = Literal["pending", "running", "finished", "error", "cancelled", "abnormal"]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Login(Input):
    username: Name
    password: str = Field(min_length=1, max_length=256)


class Project(Input):
    name: Name
    description: str = Field(default="", max_length=2000)


class Run(Input):
    mode: RunMode = "random"
    node_ids: list[ObjectId] = Field(default_factory=list, max_length=100)
    cmd: str = Field(default="", max_length=2000)
    param: str = Field(default="", max_length=4000)
    priority: int = Field(default=0, ge=-100, le=100)

    @model_validator(mode="after")
    def selected_nodes(self) -> Self:
        if self.mode == "selected-nodes" and not self.node_ids:
            raise ValueError("选择节点模式至少需要一个执行节点")
        return self


class Spider(Run):
    name: Name
    description: str = Field(default="", max_length=2000)
    project_id: ObjectId = "000000000000000000000000"
    cmd: str = Field(default="python main.py", min_length=1, max_length=2000)
    col_name: str = Field(default="", max_length=100, pattern=r"^[a-zA-Z0-9_]*$")


class Schedule(Run):
    name: Name
    description: str = Field(default="", max_length=2000)
    spider_id: ObjectId
    cron: str = Field(default="*/5 * * * *", max_length=120)
    enabled: bool = True

    @field_validator("cron")
    @classmethod
    def cron_expression(cls, value: str) -> str:
        fields = value.split()
        if len(fields) != 5:
            raise ValueError("Cron 需要五段：分 时 日 月 周")
        for field, bounds in zip(fields, [(0, 59), (0, 23), (1, 31), (1, 12), (0, 6)], strict=True):
            for item in field.split(","):
                if not re.fullmatch(r"(?:\*|[0-9]+(?:-[0-9]+)?)(?:/[0-9]+)?", item):
                    raise ValueError("Cron 支持数字、*、逗号、范围和步长")
                base, _, step = item.partition("/")
                if step and int(step) < 1:
                    raise ValueError("Cron 步长必须大于零")
                if base == "*":
                    continue
                numbers = [int(part) for part in base.split("-")]
                if not all(bounds[0] <= number <= bounds[1] for number in numbers):
                    raise ValueError("Cron 数字超出字段范围（周日为 0）")
                if len(numbers) == 2 and numbers[0] > numbers[1]:
                    raise ValueError("Cron 范围起点不能大于终点")
        return " ".join(fields)


def relative_file_path(value: str) -> str:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or "\\" in value or ":" in value or "\x00" in value:
        raise ValueError("文件路径必须是任务目录内的相对路径")
    if path == PurePosixPath("."):
        raise ValueError("请选择文件")
    return str(path)


class ScriptFile(Input):
    path: str = Field(min_length=1, max_length=240)
    content: str = Field(min_length=1, max_length=1048576)

    @field_validator("path")
    @classmethod
    def path_value(cls, value: str) -> str:
        return relative_file_path(value)

    @field_validator("content")
    @classmethod
    def content_size(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 1048576:
            raise ValueError("文件不能超过 1 MiB")
        return value
