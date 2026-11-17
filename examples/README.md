# 示例任务

`catalog/main.py` 采集项目自带的静态商品目录，产生三条记录：SKU、名称、价格和库存。页面位于 `fixture/index.html`，不依赖外部网站。

## 在 FlowHarbor 中执行

1. 启动完整 Compose 环境，确认节点列表中 Worker 在线。
2. 新建项目和任务，执行命令填写 `python main.py --url http://fixture/`。
3. 上传 `catalog/main.py`，文件名填写 `main.py`。
4. 手动执行，在任务详情中查看状态、日志及结果。
5. 新建定时计划，Cron 填写 `* * * * *` 并启用，可观察下一分钟产生的任务；验证后停用计划。

成功日志含 `FLOWHARBOR_CATALOG_SAVED count=3`，结果包含 `FH-001`、`FH-002`、`FH-003`。每次执行都会保存三条与该次任务 ID 关联的记录。

## 无需 Crawlab 的本地验证

在项目根目录打开终端运行静态站点：

```sh
python -m http.server 8099 --directory examples/fixture
```

另一个终端执行：

```sh
python examples/catalog/main.py --local --url http://localhost:8099/
```

`--local` 直接打印 JSON，不导入 SDK，不要求数据库或账号。也可运行使用真实 HTTP 服务和子进程的标准库测试：

```sh
python -m unittest discover -s examples -p "test_*.py" -v
```

## SDK 与结果存储

Worker 镜像安装 `examples/requirements.txt`。SDK 固定为 `crawlab-sdk==0.6.2`，对应本项目 Crawlab 0.6.3 的 gRPC 接口。SDK 的旧版 CLI 依赖包括 `PyYAML==6.0`，本要求文件面向镜像内的 Python 环境；本地 Python 3.12+ 请用无需 SDK 的 `--local` 验证。

Crawlab 在启动进程时注入 `CRAWLAB_TASK_ID`、`CRAWLAB_GRPC_ADDRESS`、`CRAWLAB_GRPC_AUTH_KEY`。示例通过 SDK 的同步 `save_items` 提交结果；SDK 自动添加任务 ID，Master 根据任务对应爬虫的 `col_id` 选择结果集合。FlowHarbor 创建任务时提供 `col_name`，由 Crawlab 建立集合并绑定。不要手工向脚本中写入管理员账号或数据库口令。

接口依据：[官方 Python SDK 0.6.2](https://pypi.org/project/crawlab-sdk/0.6.2/)、[官方 SDK 源码](https://github.com/crawlab-team/crawlab-sdk/tree/main/_ext/python)。完整引擎验收见 `tests/integration/README.md`。
