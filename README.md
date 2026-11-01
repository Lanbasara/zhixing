# 知行 · Zhixing

知行是一套可组合的工程技能，支持 Claude Code、Codex 和 DeepSeek Harness。

使用知行请从 [使用指南](USAGE.md) 开始，查看能力目录、调用方式与共享原则；
安装与升级见 [INSTALL.md](INSTALL.md)。

## 开发与交付

本仓库保存产品内容源、构建工具与开发约定。`USAGE.md` 是面向使用者的说明，
构建时作为安装包的 `README.md`；本文件只作为源码仓入口，不进入安装包。
`skills/`、`principles/`、`references/` 是内容维护源；`plugin/` 是生成并跟随 PR
审阅的安装包，不能手工编辑。版本只在 `VERSION` 维护。

从最新 `origin/main` 建任务分支，执行本地检查后提交 PR。仓库开发约定见
[AGENTS.md](AGENTS.md)，结构见 [架构说明](docs/architecture.md)，
发布见 [RELEASING.md](RELEASING.md)。

```sh
python3 -m pip install -r scripts/requirements-check.txt
python3 scripts/check.py
python3 scripts/bundle.py --out /path/to/new-package
python3 scripts/qa.py --package /path/to/new-package
# 新包验证通过后更新 plugin/，再运行完整的 PR 门禁：
python3 scripts/qa.py
```

维护需要 Python 3.11+、Node.js 22+ 和 npm；技能使用无需运行这些开发工具。
静态检查与离线测试验证内容、调用策略和打包契约。技能质量采用
[独立任务检验](evaluations/README.md)，真实宿主发现与调用另行验收；CI 通过
不代表已完成模型行为评价或实际安装。AI 与联网验收记录实际范围，不作为自动门禁。
