# 第三方组件说明

FlowHarbor（流港调度）包含原创产品界面和接入服务，使用 Crawlab 作为调度引擎。FlowHarbor 并非 Crawlab 官方产品，也不代表 Crawlab 团队背书。

| 组件 | 用途 | 上游许可 / 来源 |
| --- | --- | --- |
| Crawlab 0.6.3 | 调度、运行节点、代码同步、日志、结果 | BSD-3-Clause，完整文本见 `licenses/Crawlab-BSD-3-Clause.txt`；https://github.com/crawlab-team/crawlab |
| Crawlab SDK 0.6.2 | Python 采集结果提交 | BSD-3-Clause，完整文本见 `licenses/Crawlab-SDK-BSD-3-Clause.txt`；https://github.com/crawlab-team/crawlab-sdk |
| Vue | 管理界面 | MIT；https://github.com/vuejs/core |
| Vite | 前端构建 | MIT；https://github.com/vitejs/vite |
| TypeScript | 前端类型检查 | Apache-2.0；https://github.com/microsoft/TypeScript |
| FastAPI / Pydantic / HTTPX / Uvicorn | 接入服务 | MIT / MIT / BSD-3-Clause / BSD-3-Clause；以对应安装包许可为准 |
| MongoDB Community | Crawlab 元数据存储 | SSPL；https://www.mongodb.com/legal/licensing/server-side-public-license |
| Nginx | 静态文件及反向代理 | BSD-2-Clause；https://nginx.org/LICENSE |
| Python / Node.js | 运行环境 | PSF / Node.js及其第三方许可；以镜像内附许可为准 |

依赖锁文件记录实际安装版本。容器基础镜像及传递依赖保留各自的许可，不能以本项目的专有许可替代。交付源码包不包含第三方容器镜像；部署时从上游镜像仓库下载。

发布前按照锁文件生成前端许可清单，按 Python 安装环境生成后端许可清单，并随源码交付。生成方法见 `docs/release.md`。上述表格是直接组件说明，完整清单以生成的报告为准。
