# 部署、升级和数据维护

## 1. 运行环境

使用 Linux amd64 云服务器或 Docker Desktop 的 Linux 容器环境，安装 Docker Compose v2。首个版本使用单 Master、两个 Worker。建议从 4 核 CPU、8 GB 内存、20 GB 可用磁盘开始，并根据任务运行时占用调整；这属于部署建议，尚无容量基准测试。

首次构建需要下载 Crawlab、MongoDB、Python、Node.js、Nginx 镜像与包依赖。镜像版本在 `compose.yaml` 和 `deploy/*.Dockerfile` 固定；引擎运行镜像额外安装 `examples/requirements.txt` 中的 SDK。

## 2. 本机启动

在仓库根目录执行：

```bash
python scripts/configure.py
docker compose config --quiet
docker compose up -d --build
docker compose ps
docker compose logs --tail=100 master api
```

配置脚本只创建尚不存在的 `.env`，不会覆盖已有部署密码。它生成 MongoDB 密码、节点共享密钥及浏览器会话密钥。

- 产品界面：`http://localhost:8080`
- Crawlab 原生控制台：`http://localhost:18080`（仅本机）
- 初始 Crawlab 用户名 / 密码：`admin` / `admin`，来自该版本官方初始化逻辑。

先在本机原生控制台登录并修改管理员密码，再用新密码登录 FlowHarbor。账号管理沿用 Crawlab，FlowHarbor 不另外创建账号库。等待节点页出现 Master 与两个 Worker 在线后，按 [操作手册](user-guide.md) 导入样例。

`/api/health` 仅表明接入服务存活。引擎是否可用，以成功登录、节点在线和实际任务完成为准。

## 3. 域名访问

将现有 HTTPS 反向代理指向服务器的 `127.0.0.1:8080`，保留原始 Host 和 Origin。设置：

```dotenv
PUBLIC_ORIGIN=https://collect.example.com
COOKIE_SECURE=true
```

然后 `docker compose up -d api`。将示例域名替换为自己的域名。若修改入口端口，同步修改 `WEB_PORT` 和 `PUBLIC_ORIGIN`；浏览器必须使用与配置完全相同的协议、主机和端口。原生控制台可通过 SSH 端口转发访问：

```bash
ssh -L 18080:127.0.0.1:18080 user@your-server
```

## 4. 日常操作

```bash
docker compose logs --tail=100 worker-01
docker compose restart api
docker compose stop
docker compose start
```

`stop` 和 `start` 保留卷；不要用 `down -v` 作为日常重启命令，因为该选项会删除数据卷。

## 5. 一致性备份

以下命令使用 Linux Bash。备份时暂停任务写入；计划在停止期间不会按原时间执行，需要按业务情况补跑。备份目录同时含账号数据库和 `.env`，应保存在私有备份位置。

```bash
mkdir -p backups
docker compose stop web api worker-01 worker-02 master
docker compose exec -T mongo sh -c 'mongodump --username "$MONGO_INITDB_ROOT_USERNAME" --password "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin --db crawlab --archive=/tmp/flowharbor.archive --gzip'
docker compose cp mongo:/tmp/flowharbor.archive backups/flowharbor.archive
docker compose cp master:/data backups/master-data
docker compose cp master:/root/.crawlab backups/master-identity
docker compose cp worker-01:/root/.crawlab backups/worker-01-identity
docker compose cp worker-02:/root/.crawlab backups/worker-02-identity
cp .env backups/deployment.env
docker compose start master worker-01 worker-02 api web
```

## 6. 恢复到全新部署

将备份和同版本源码复制到新的空部署目录，恢复原 `.env`，创建容器与卷，再导入数据。此流程面向空目标，避免覆盖正在使用的实例。

```bash
cp backups/deployment.env .env
docker compose build
docker compose up -d --wait mongo
docker compose create master worker-01 worker-02 api web fixture
docker compose cp backups/flowharbor.archive mongo:/tmp/flowharbor.archive
docker compose exec -T mongo sh -c 'mongorestore --username "$MONGO_INITDB_ROOT_USERNAME" --password "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin --archive=/tmp/flowharbor.archive --gzip'
docker compose cp backups/master-data/. master:/data/
docker compose cp backups/master-identity/. master:/root/.crawlab/
docker compose cp backups/worker-01-identity/. worker-01:/root/.crawlab/
docker compose cp backups/worker-02-identity/. worker-02:/root/.crawlab/
docker compose up -d
```

登录后核对项目、任务、计划、历史结果和节点在线状态，再手动执行一次示例。备份恢复命令尚需在实际 Docker 环境验收，不能只凭备份文件存在就认定恢复成功。

## 7. 常见问题

| 现象 | 检查方式 |
| --- | --- |
| 登录提示引擎不可达 | 查看 master 启动日志与 MongoDB 健康状态 |
| 修改请求被拒绝 | 浏览器来源是否等于 `PUBLIC_ORIGIN`；HTTPS 是否正确设置 cookie |
| Worker 不在线 | 检查 `CRAWLAB_GRPC_ADDRESS`、共享密钥和主节点日志 |
| 有日志但没有结果 | 脚本是否调用 `crawlab.save_item`，任务是否绑定结果集合 |
| 任务一直 pending | 节点是否在线、任务选择的节点是否存在、运行槽是否已占满 |
| 上传中文脚本失败 | 文件是否为 UTF-8、是否小于 1 MiB、路径是否相对路径 |

## 8. 本地开发

后端在 `backend/` 安装 `requirements-dev.txt`，设置 `CRAWLAB_BASE_URL=http://localhost:18080/api`、`FLOWHARBOR_PUBLIC_ORIGIN=http://localhost:5173` 和随机 `FLOWHARBOR_SESSION_SECRET`，执行 `uvicorn app.main:app --reload`。前端在 `frontend/` 执行 `pnpm install --frozen-lockfile`、`pnpm dev`，Vite 将 `/api` 代理到后端。

开发环境的引擎依旧需要真实 Crawlab；API 连接失败不会自动切换成演示数据。
