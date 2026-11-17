# 验证记录

日期：2026-11-13。版本：FlowHarbor 0.1.0。

本次先交付源码，完整引擎验收按用户安排留到 Windows Docker 环境执行。本记录区分源码与浏览器检查、HTTP 边界检查和真实调度检查。

## 已执行并通过

| 检查 | 结果 | 实际范围 |
| --- | --- | --- |
| Vue / TypeScript 检查与 Vite 生产构建 | 通过 | 全部前端源码，生产 JS 约 127 kB / gzip 45 kB |
| 后端 pytest | **31 passed** | 实际 FastAPI 实现 + 本地 HTTP fixture；认证、来源校验、ID/文件/Cron 校验、请求映射、引擎错误、计划编辑、字面搜索及结果保真 |
| 后端 Ruff | 通过 | app 和 tests |
| Python 依赖一致性 | 通过 | `pip check` 无冲突，运行依赖锁定为实际安装版本 |
| 示例采集 unittest | **1 passed** | 真正启动本地 HTTP 页面，通过子进程执行采集脚本并验证 3 条商品 |
| Playwright / Chrome | **3 passed** | 实际 FastAPI + Vite；未登录导航、真实引擎不可达提示、390px 页面无水平溢出 |
| 界面视觉检查 | 通过 | 1440×960 桌面、390×844 手机登录页截图 |
| Python 编译检查 | 通过 | 后端、示例、测试及脚本 |
| YAML 解析 | 通过 | Compose 与两份 GitHub Actions 工作流，仅语法与锚点解析 |
| PowerShell 脚本解析 | 通过 | `scripts/test-windows.ps1`；完整安装流程未重复执行 |
| pnpm 10.6.2 锁文件兼容检查 | 通过 | 在独立目录使用 `--lockfile-only --frozen-lockfile` 校验 |
| 源码交付包检查 | 通过 | ZIP 完整性、实际部署密钥未混入、无依赖缓存和 Git 历史、文档内部链接有效 |

Windows 测试环境：Python 3.12.14、Node.js 24.22.1、pnpm 11.25.0、已安装的 Chrome。浏览器测试使用发布固定版本 FastAPI 0.115.12、Pydantic 2.11.4；没有换用其他版本替代验证。交付的容器构建采用 Node.js 22.14.0、pnpm 10.6.2，尚未执行容器构建。

pytest 输出一条 Starlette 对 AnyIO 别名的弃用提示，不影响这 31 项测试结果。

## 尚未执行的验收

- 当前电脑未提供可运行的 Docker Engine / Docker Desktop，因此未运行 `docker compose config`、镜像构建或完整栈启动。
- `tests/integration` 实际结果为 **1 skipped**，并非通过。该脚本需显式开启后才能连接真实引擎。
- 尚未验证固定镜像内的 Python/SDK 安装、Worker 注册、脚本同步、真实手动执行、结果入库、Cron 触发和取消流程。
- 重启持久化、备份恢复和真实部署容量尚未运行验收。
- GitHub Actions 工作流已交付，尚未上传远程仓库或执行 CI。

固定 Crawlab 0.6.3 的接口与源码已核对，镜像标签和摘要已从官方 Docker Hub 核对。这些源码检查不替代实际引擎执行。

## 下一步

按 [Windows 测试指南](windows.md) 配置 Docker Desktop 的 Linux 容器模式，启动完整栈并执行真实集成测试；将结果追加到本记录。商品演示中的实际调度效果应以该次验收为准。

当前截图仅展示实际登录界面，没有使用构造业务数据伪装运行成果。
