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
| 人工入口 | [setup](skills/setup/SKILL.md) | 建立适合项目的协作入口、知识结构和验证入口 |
| 人工入口 | [align](skills/align/SKILL.md) | 先研究，再围绕有影响的歧义与人深入讨论 |
| 人工入口 | [specify](skills/specify/SKILL.md) | 将已确认的意图与决定写成可检验的规格 |
| 人工入口 | [plan](skills/plan/SKILL.md) | 设计有反馈的实现切片、依赖与集成路径 |
| 人工入口 | [implement](skills/implement/SKILL.md) | 持续实现、集成、验证，直到完成或真实阻塞 |
| 人工入口 | [evolve](skills/evolve/SKILL.md) | 从实际问题改进方法，检验改动能否迁移 |
| 按需组合 | [research](skills/research/SKILL.md) | 调查代码、历史理由和外部依据 |
| 按需组合 | [model](skills/model/SKILL.md) | 澄清领域概念、状态、归属和模块接口 |
| 按需组合 | [constrain](skills/constrain/SKILL.md) | 让结构或检查承担重要工程约束 |
| 按需组合 | [verify](skills/verify/SKILL.md) | 设计并执行验证，维护可复用的用户路径 |
| 按需组合 | [review](skills/review/SKILL.md) | 审查实际差异、缺陷与受影响行为 |
| 按需组合 | [debug](skills/debug/SKILL.md) | 建立反馈、定位原因，按授权修复和验证 |
| 按需组合 | [prototype](skills/prototype/SKILL.md) | 用 HTML 原型检验具体设计假设 |
| 按需组合 | [explain](skills/explain/SKILL.md) | 用 HTML 解释方案、关系和取舍 |
| 按需组合 | [report](skills/report/SKILL.md) | 用 HTML 组织结论、证据和实际限制 |

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

## 安装与命名

三个宿主使用同一份 [技能](skills/)，安装入口见 [INSTALL.md](INSTALL.md)。
技能使用 `align`、`plan` 等短名；请按所用宿主选择或调用：

| 宿主 | 人工调用示例 |
| --- | --- |
| Claude Code | `/zhixing:align` |
| Codex / ChatGPT 桌面 | 选择知行插件中的 `align` 技能 |
| DSH | `/zhixing-align` |

0.2.0 将源码技能从 `zhixing-align` 一类名称改为 `align`，并把安装根目录移到
`plugin/`。升级后使用新的调用名；不保留重复注册的旧别名。
六个人工入口在三个宿主中都关闭自动调用，其余能力保持可按需组合。

## 思想来源

知行吸收 [Matt Pocock 的 skills](https://github.com/mattpocock/skills) 中的深入对齐、
领域建模、曳光弹与上下文管理；其
[Writing for Agents](https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-for-agents/SKILL.md)
进一步启发了阅读入口、信息组织、完成判断和指令贡献的表达。
[pstack](https://github.com/cursor/plugins/tree/main/pstack) 对真实反馈、
[可复跑验证方法](https://github.com/cursor/plugins/blob/main/pstack/skills/create-verification-skill/SKILL.md)
和可执行约束的重视也被融入知行；同时吸收了 Jianwei 实践中关于专业责任、
最小自洽指导和防止技能过拟合的判断。

这些思想经过重新组织，不以复刻原仓库的目录或流程为目标。DRY 关注知识的维护源，
曳光弹强调真实贯通的反馈；可继续阅读作者关于 [DRY](https://media.pragprog.com/titles/tpp20/dry.pdf)
与 [原型和曳光弹](https://www.artima.com/articles/tracer-bullets-and-prototypes) 的说明。
