# 真实引擎集成验收

本测试连接已启动的 FlowHarbor、Crawlab Master、Worker、MongoDB 和 fixture HTTP 服务。不会使用模拟响应；未显式启用时显示 `skipped`。没有 Docker 环境时，不能将跳过测试描述为集成测试通过。

前提：完整 Compose 服务已启动，至少一个 Worker 在线；已设置可登录的 Crawlab 账号；测试客户端安装后端开发依赖中的 `pytest` 和 `httpx`。从项目根目录执行。

PowerShell：

```powershell
$env:FLOWHARBOR_INTEGRATION = "1"
$env:FLOWHARBOR_TEST_URL = "http://localhost:8080"
$env:FLOWHARBOR_TEST_USERNAME = "你的账号"
$env:FLOWHARBOR_TEST_PASSWORD = "你的口令"
python -m pytest tests/integration -v
```

Bash：

```sh
export FLOWHARBOR_INTEGRATION=1
export FLOWHARBOR_TEST_URL=http://localhost:8080
export FLOWHARBOR_TEST_USERNAME='你的账号'
export FLOWHARBOR_TEST_PASSWORD='你的口令'
python -m pytest tests/integration -v
```

测试行为：登录，选择在线 Worker，创建独立项目和任务，上传并回读脚本，真实执行，确认指定节点、完成状态、三条结果和日志；创建每分钟 Cron，修改启用中的计划并重复启用，等待自动任务，停用后跨过下一分钟确认无新任务，以检查旧调度条目是否被清理。通常需 2–4 分钟。HTTP 请求超时 30 秒，单次任务完成上限 180 秒。

测试使用唯一项目名，结束时尝试删除自身创建的计划、任务定义和项目；若任务仍在运行，后端会拒绝删除，需检查该临时项目后手工处理。Crawlab 的任务历史及结果集合可能保留，便于检查；本测试不清理其他项目数据。测试过程请勿手工修改这些临时资源。

如果失败，保留终端错误以及 `docker compose logs master worker-01 worker-02 api` 输出。容器中的实际 Python/SDK 安装、节点文件同步和 SDK 结果入库必须由本测试确认，单独通过 `--local` 示例不代表这些链路已通过。
