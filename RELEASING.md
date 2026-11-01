# 知行的开发与发布

知行源码仓负责产品和 Release，`Lanbasara/zhixing-marketplace` 负责安装索引。
本文件描述仓库维护，不改变使用知行时的技能组合方式。

## 开发与 PR

从最新 `origin/main` 创建 `codex/<任务名>` 分支或独立 worktree。主工作树保持
main 和干净；不要修改其他项目。修改内容源，运行 `scripts/check.py`，在新目录
构建并运行 `scripts/qa.py --package <目录>`，通过后才替换已生成的 `plugin/`。
提交前运行 `scripts/qa.py`，包括实际 npm 打包验证和发布对象测试。

使用 gh 推送分支、提交 PR、等待 `package (3.11)` 与 `package (3.13)`。
main 要求通过 PR、必需检查和讨论解决后才能更新，禁止强推与删除。
PR 的 Actions artifact 是基于该次合并测试提交的预览，不是正式发行。
合入 main 后的候选需按 main 的精确提交重新验证。

`VERSION` 唯一维护版本；其他版本字段由构建器生成。0.x 的 minor 可包含已说明
的调用名或安装布局变化，patch 用于兼容修复；1.x 起不兼容变化提升 major。
版本、内容源、生成包与安装说明在同一个 PR 中更新。

## 发布候选

在 main 上使用 gh 运行 Release workflow 的 workflow_dispatch。该事件永远只
构建预览，没有写权限或 publish job。按运行的 commit 下载
`zhixing-release-<完整 SHA>` 到新目录，并验证：

```sh
python3 scripts/release.py --ref FULL_MAIN_SHA --verify /path/to/download
```

验证器从该提交的 Git 对象重新生成 ZIP、release.json 和 SHA256SUMS，逐字节
核对下载物；工作树未提交内容不影响候选。根据改动记录真实宿主加载、调用与
行为检验情况，未执行的部分明确写出。AI、联网验收不进入自动门禁。

## 正式发行

只有明确发布授权才创建版本标签。发布前记录版本、main 的精确 commit、候选
运行与摘要、检查结论、市场 main 的精确 commit、待执行的外部动作。
已有授权覆盖这些对象时连续执行；影响发布身份或范围的变化需要重新确认。

1. 确认源提交位于 main、版本未发布、候选验证通过、GitHub 保护实际生效。
2. 在精确源提交创建 annotated `v<VERSION>` 并推送。标签规则禁止修改和删除。
3. tag workflow 重跑离线 QA，从已提交的 plugin/ 构建正式发行包，另生成
   三端市场候选；两种 artifact 分开保存。
4. 下载并通过 `scripts/release.py --ref vVERSION --official --verify <目录>` 核对
   正式 artifact。确认远端 annotated tag 指向原提交、工作流对应同一提交。
5. 批准该运行的 `source-release` 环境后，publish 才取得 contents:write，创建
   不可变 GitHub Release。检查附件、标签和来源信息，核对下载的实际字节。

source-release 只接受版本标签，必须由维护者批准，禁止管理员绕过。环境批准
只针对本次已核验的运行；不能把另一个运行的成功当作当前运行的证据。
仓库启用不可变 Releases。源码工作流没有市场仓写权限，也不创建市场 PR。

## 市场交付

Release 成功后，下载同一 tag 运行的 `zhixing-marketplace-<SHA>`。
在市场仓先 fetch main，确认 candidate.json 中的 marketplaceBase 仍等于
origin/main；同时核对 sourceCommit、tag 和四个文件摘要。用同一不可变 tag 与
该市场基线本地重建候选，比较下载物，防止拿错 artifact。

```sh
python3 scripts/marketplace.py --tag vVERSION --marketplace /path/to/market-main --out /path/to/new-candidate
```

在市场仓从该 main 建新分支，只更新 releases.json 和三端索引四个文件。
运行市场仓验证器，提交独立 PR，等待必需检查后按授权合并。
市场 CI 会拒绝历史改写；新索引固定源 commit 和 plugin/ 子目录。
主仓与市场仓的完成状态分别记录：源 Release 成功、市场失败时，不能报告全部交付。

市场基线变化时保留已有 Release；基于新基线重新生成和审阅市场候选。
产品变化必须走新版本，禁止移动标签、覆盖 Release 或绕过检查。

## 维护者入口与证据

[zhixing-release](.agents/skills/zhixing-release/SKILL.md) 帮助维护者完成预检、发布
与失败接续，仅在源码仓发现，不进入安装包。
发布记录放 PR、Release 或外部实验记录，至少保留版本、源码与市场 commit、
工作流运行、PR、artifact 摘要、自动与手工验证范围。凭据不进入记录。
