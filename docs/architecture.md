# 知行的内容与交付结构

知行提供 15 个可组合技能，没有运行服务、任务数据库或工作流引擎。
宿主负责发现和调用，项目拥有事实，agent 根据用户目标组织工作。

## 内容与宿主

`skills/<短名>/SKILL.md` 是唯一技能正文；`PHILOSOPHY.md`、`principles/`、
`references/` 保存共享判断与约定。正文保留相对引用，三端安装相同字节。
调用策略由技能 frontmatter 表达，现有 Codex policy 与之核对；DSH 目录从
frontmatter 生成。Claude/Codex 负责插件命名空间，DSH 的平面注册表由
`adapters/dsh.mjs` 添加一次 `zhixing-`，适配层不实现技能的专业行为。

六个人工入口只由用户发起；另外九个能力可按需组合。入口约束不成为普通
编码任务的审批步骤。知行仓库自己的交付流程也不进入这些通用技能正文。

## 可验证的安装包

`VERSION` 是版本唯一维护源；`distribution.json` 描述身份与 DSH 兼容范围。
`scripts/bundle.py` 收集明确的内容目录与共享文件，生成三个宿主的清单、
DSH catalog、package.json 和完整文件摘要 manifest.json。

在仓库外构建新目录，用 `scripts/qa.py --package <新目录>` 验证后才替换
受版本管理的 `plugin/`。构建器拒绝覆盖目标、链接资源和越界路径。
`plugin/` 的路径、字节和权限必须与重建结果一致；开发工具、维护技能、
实验和凭据不进入包。npm 真正打包后的内容必须与这个目录完全一致。

README、安装文档与行为检验方法随包分发，因为它们用于理解与检验技能。
开发约定、架构、CI、发布脚本和 `.agents/skills/zhixing-release/` 只留在源码仓。

## 开发与发布

任务分支从最新 main 开始。PR 与 main push 执行相同的离线门禁，并生成可下载
候选；候选只用于审阅。正式发布从 main 可达的 annotated stable tag 读取
已提交 Git 对象，重验完整 manifest，生成确定性 ZIP 与来源记录。
GitHub 的受保护发布环境批准后，发布任务才取得写权限。

市场仓维护三端分发索引，不保存技能正文。源码工作流只能产生市场候选，
维护者在 Release 成功后通过市场仓独立 PR 更新。具体操作见
[发布约定](../RELEASING.md)。

## 证据边界

CI 证明内容、命名、注册、打包和发布对象契约；实际宿主发现、人工与自动调用、
模型表现分别需要运行证据。行为评估方法见 [evaluations](../evaluations/README.md)，
评估与联网检查保持人工选择，原始证据在仓库外保存。
