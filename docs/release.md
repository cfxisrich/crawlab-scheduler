# GitHub 与买家交付

## 私有仓库

在 GitHub 新建 **Private** 仓库，不添加远程 README 或 LICENSE。确认本地 `.env`、缓存、备份与运行数据被忽略，再提交：

```bash
git status --short
git add .
git diff --cached --stat
git commit -m "Initial FlowHarbor source delivery"
git remote add origin git@github.com:YOUR_ACCOUNT/flowharbor.git
git push -u origin main
```

将 `YOUR_ACCOUNT` 替换为自己的 GitHub 账号。仓库已在本地初始化为 main；若从 ZIP 解压且没有 `.git`，先执行 `git init -b main`。推送及远程仓库创建由仓库拥有者执行，本地交付不代表已经上传。

## 验证后发布

普通推送触发 `Build and test`，执行前端构建、后端测试、示例测试、Compose 配置检查与镜像构建。Actions 中手动运行 `Live Crawlab acceptance`，会在临时 Linux 环境启动完整栈，验证采集结果和 Cron；任务结束删除该 CI 临时数据卷。

实际售卖前，应保留自己的完整部署验收结果。项目中的 `docs/verification.md` 记录本次制作环境的已测项和未测项，不能把 CI 文件存在当作 CI 已通过。

## 依赖与许可清单

前端生产依赖：

```bash
cd frontend
pnpm licenses list --prod --json > ../licenses/frontend-dependencies.json
```

后端在只安装 `backend/requirements.lock` 的 Python 环境中，用 Python 的 `importlib.metadata` 或许可清单工具导出已安装包版本和许可。当前源码包已经包含前端与后端运行依赖的清单及许可文本。基础镜像及 SDK 仍以镜像内实际安装清单为准。交付时保留 `licenses/`、`THIRD_PARTY_NOTICES.md` 和依赖锁文件。

## 打包

在根目录运行：

```bash
python scripts/package_release.py
```

输出 `release/flowharbor-0.1.0-source.zip` 和 `release/SHA256SUMS.txt`。脚本按明确目录清单收集源码，排除 `.env`、Git 历史、依赖目录、构建缓存及备份。ZIP 内不打包第三方镜像；买家部署时下载。

交付包应附带产品版本、购买授权、部署手册、使用手册和与本版本匹配的验证记录。授权主体、部署数量、是否允许买家转售及售后期限由你填写，仓库未假定这些商业条款。

## 商品页面

可从 `docs/product.md` 取用介绍文案，使用 `docs/screenshots/` 中实际界面截图。上传目标平台时填写真实功能与运行条件；录制真实采集和定时执行流程后，可将演示视频链接加入商品说明。
