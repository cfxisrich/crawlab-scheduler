# Windows 测试指南

测试分为本机源码/浏览器验证和 Docker 中的真实调度验证。前者不需要 Crawlab 在线；后者会实际启动 Master、两个 Worker、MongoDB 和示例站点。

## 本机测试

安装 Python 3.12、Node.js 22（至少 22.12）、pnpm 10.6.2、PowerShell 7.4+。从源码根目录运行：

```powershell
pwsh -File scripts/test-windows.ps1 -Python 'C:\Python312\python.exe'
```

将 Python 路径改为实际安装位置。脚本创建项目内 `.venv`，安装固定后端依赖，执行后端测试、标准库采集示例测试、前端构建，并安装 Playwright Chromium 运行浏览器测试。首次执行需要下载依赖和浏览器。

浏览器测试自动启动 `127.0.0.1:8181` 的真实接入服务和 `127.0.0.1:5181` 的前端。它验证未登录导航、引擎不可达时的真实错误提示、桌面与手机宽度布局；测试没有使用可运行的采集引擎，因此不能替代调度验收。

测试截图位于 `docs/screenshots/`。后端测试使用真实本地 HTTP 服务验证请求和响应边界，但该服务不是 Crawlab。

## Windows Docker Desktop 调度验收

安装并启动 Docker Desktop，使用 **Linux containers / WSL 2 backend**。在 PowerShell 运行以下命令，确认客户端和服务端均可用：

```powershell
docker version
docker compose version
```

从项目根目录启动：

```powershell
python scripts/configure.py
docker compose config --quiet
docker compose up -d --build
docker compose ps
```

如果已经生成 `.env`，跳过配置脚本。当前固定 Crawlab 镜像为 `linux/amd64`。打开 `http://localhost:18080`，用初始 `admin/admin` 登录后修改密码，再打开 `http://localhost:8080` 登录 FlowHarbor。等待两个 Worker 在线。

启用真实集成测试：

```powershell
$env:FLOWHARBOR_INTEGRATION = '1'
$env:FLOWHARBOR_TEST_URL = 'http://localhost:8080'
$env:FLOWHARBOR_TEST_USERNAME = 'admin'
$credential = Get-Credential -UserName admin -Message '输入修改后的 Crawlab 密码'
$env:FLOWHARBOR_TEST_PASSWORD = $credential.GetNetworkCredential().Password
.\.venv\Scripts\python.exe -m pytest tests/integration -v
Remove-Item Env:FLOWHARBOR_TEST_PASSWORD
```

测试验证上传脚本、指定 Worker 运行、三条结果入库、日志、修改定时计划和停用计划。完整过程通常几分钟。出现失败时保存终端结果以及以下服务日志：

```powershell
docker compose logs --tail=200 master worker-01 worker-02 api
```

最后执行 `docker compose restart`，再次登录核对项目、计划和历史结果仍然存在，并手动运行样例。重启持久化属于单独验收步骤，测试脚本不会自动重启你的整个环境。
