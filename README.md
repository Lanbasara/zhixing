# 知行 · Zhixing

一套可组合的工程技能，帮助人与 agent 澄清意图、作出判断，并把判断变成可验证的成果。
技能定义专业责任和完成的含义，保留方法、顺序、工具与协作方式的选择空间。

知行没有必须走完的流水线。简单问题可以直接解决；复杂工作可以经过讨论、规格、
计划和实现，也可以沿用项目已有的方法。已有上下文足够时直接工作；跨会话接续时，
只恢复当前任务需要的知识。Spec 按需要使用，不依赖工单系统。

## 能力与调用

六个人工入口只在用户主动发起相应工作时使用。其余能力允许 agent 按任务需要选用，
也可以由用户直接调用。人工入口不是普通工作的审批门槛：实现中的内部规划、调查和
调试可以继续，普通编码请求也无需先调用知行。

| 调用方式 | 能力 | 职责 |
| --- | --- | --- |
| 人工入口 | [setup](skills/zhixing-setup/SKILL.md) | 建立适合项目的协作入口、知识结构和验证入口 |
| 人工入口 | [align](skills/zhixing-align/SKILL.md) | 先研究，再围绕有影响的歧义与人深入讨论 |
| 人工入口 | [specify](skills/zhixing-specify/SKILL.md) | 将已确认的意图与决定写成可检验的规格 |
| 人工入口 | [plan](skills/zhixing-plan/SKILL.md) | 设计有反馈的实现切片、依赖与集成路径 |
| 人工入口 | [implement](skills/zhixing-implement/SKILL.md) | 持续实现、集成、验证，直到完成或真实阻塞 |
| 人工入口 | [evolve](skills/zhixing-evolve/SKILL.md) | 从实际问题改进方法，检验改动能否迁移 |
| 按需组合 | [research](skills/zhixing-research/SKILL.md) | 调查代码、历史理由和外部依据 |
| 按需组合 | [model](skills/zhixing-model/SKILL.md) | 澄清领域概念、状态、归属和模块接口 |
| 按需组合 | [constrain](skills/zhixing-constrain/SKILL.md) | 让结构或检查承担重要工程约束 |
| 按需组合 | [verify](skills/zhixing-verify/SKILL.md) | 设计并执行验证，维护可复用的用户路径 |
| 按需组合 | [review](skills/zhixing-review/SKILL.md) | 审查实际差异、缺陷与受影响行为 |
| 按需组合 | [debug](skills/zhixing-debug/SKILL.md) | 建立反馈、定位原因，按授权修复和验证 |
| 按需组合 | [prototype](skills/zhixing-prototype/SKILL.md) | 用 HTML 原型检验具体设计假设 |
| 按需组合 | [explain](skills/zhixing-explain/SKILL.md) | 用 HTML 解释方案、关系和取舍 |
| 按需组合 | [report](skills/zhixing-report/SKILL.md) | 用 HTML 组织结论、证据和实际限制 |

例如，可以先请 align 澄清一个领域问题，之后独立调用 specify；也可以直接请
implement 按已有目标完成改动。要求一个已有方案的 HTML 说明时，explain 可以
直接从提供的材料开始，无需恢复整项工程。

人工入口约束决定谁发起工作模式，不意味着每个技术步骤都要再次确认；它也不替代
宿主权限、项目约定或用户授权。

## 原则与项目知识

[PHILOSOPHY.md](PHILOSOPHY.md) 指向共享原则：责任与范围、知识与局部理解、
推理与约束、反馈与真实路径、变化与责任层，以及技能设计。它们同时指导知行自身
的维护与外部工程工作，只维护一套，并按问题读取。

项目拥有自己的事实与决定。知行提供 [知识职责约定](references/project-knowledge.md)，
适配现有 AGENTS、架构、ADR、spec、feature map 与验证材料；这些职责不要求对应
一套必建文件。恢复工作参照 [上下文约定](references/context.md)，验证方法参照
[验证约定](references/verification.md)。

## 使用源码包

仓库本身是插件内容，无构建步骤。保留完整目录；不要只复制单个 `SKILL.md`，因为
技能会引用同包中的共享材料。源码不会自动安装或修改项目、全局配置。

Claude Code 可在单次会话中加载本地目录：

```sh
claude --plugin-dir /path/to/zhixing
```

加载后，人工入口示例为 `/zhixing:zhixing-align`。
本地插件加载方式见 [Claude Code 官方文档](https://code.claude.com/docs/en/plugins/create)。

Codex 使用 `.codex-plugin/plugin.json` 发现同一组技能；安装后调用示例为
`$zhixing-align`。本地使用可将完整源码包放在目标项目的 `plugins/zhixing/`，
并在该项目的 `.agents/plugins/marketplace.json` 中添加 marketplace 条目。例如：

```json
{
  "name": "local-engineering",
  "plugins": [{
    "name": "zhixing",
    "source": {"source": "local", "path": "./plugins/zhixing"},
    "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
    "category": "Productivity"
  }]
}
```

已有 marketplace 时合并条目。`source.path` 相对目标项目根目录解析。
重启支持本地 marketplace 的 ChatGPT 桌面宿主，在 Plugins 中选择该来源并安装，
随后在新会话中使用；Codex CLI 可用 `/plugins` 浏览已配置的 marketplace。
具体能力与版本要求参照 [Codex 插件文档](https://developers.openai.com/plugins/build/plugins)
和 [插件使用文档](https://learn.chatgpt.com/docs/plugins)。以上配置由使用者按需执行。

六个人工入口同时提供 Claude 的 `disable-model-invocation` 与 Codex 的
`allow_implicit_invocation: false`，其余能力沿用自动选择默认值。

## 维护与检验

维护入口为 [AGENTS.md](AGENTS.md)，内容组织见 [架构说明](docs/architecture.md)。
本地检查只需要 Python 和 PyYAML；这些是维护依赖，使用技能无需运行它们。

```sh
python3 -m pip install -r scripts/requirements-check.txt
python3 scripts/check.py
claude plugin validate . --json
```

检查器验证包结构、调用策略和资源引用，不评价哲学是否正确或 agent 是否表现良好。
行为质量采用 [独立任务检验](evaluations/README.md)；实际实验保留各自的版本、环境
和证据，不能由静态检查通过推导运行效果。宿主版本变化时，需要重新确认加载与
调用策略。

## 思想来源

知行吸收 [Matt Pocock 的 skills](https://github.com/mattpocock/skills) 中的深入对齐、
领域建模、曳光弹与上下文管理，以及 [pstack](https://github.com/cursor/plugins/tree/main/pstack)
对真实反馈、验证能力和可执行约束的重视；也吸收了 Jianwei 实践中关于专业责任、
最小自洽指导和防止技能过拟合的判断。

这些思想经过重新组织，不以复刻原仓库的目录或流程为目标。DRY 关注知识的维护源，
曳光弹强调真实贯通的反馈；可继续阅读作者关于 [DRY](https://media.pragprog.com/titles/tpp20/dry.pdf)
与 [原型和曳光弹](https://www.artima.com/articles/tracer-bullets-and-prototypes) 的说明。
