# 使用知行

安装完整的 `plugin/` 目录或正式 Release 中的 `zhixing-plugin.zip` 解压结果。
技能引用同包的共享材料，不能只拷贝某个 SKILL.md。源码根目录用于维护，
从源码试用前运行构建并验证新包，或使用随提交审阅的 `plugin/`。

## Claude Code

单次会话可加载本地包，不修改全局安装：

```sh
claude --plugin-dir /path/to/zhixing/plugin
```

调用例子为 `/zhixing:align`、`/zhixing:implement`。
正式版本进入市场后，可添加 `Lanbasara/zhixing-marketplace` 并安装 `zhixing@zhixing`。

## Codex 与 ChatGPT 桌面

包提供通用 plugin.json 与 Codex 兼容清单。技能使用短名，在插件选择器中选择
知行插件的 `align`、`plan` 等技能；具体命令呈现以宿主为准。

本地 marketplace 的 source.path 指向完整包，例如项目根目录下的 `./plugins/zhixing`：

```json
{
  "name": "local-engineering",
  "plugins": [{
    "name": "zhixing",
    "source": {"source": "local", "path": "./plugins/zhixing"},
    "policy": {"installation": "AVAILABLE", "authentication": "ON_USE"},
    "category": "Productivity"
  }]
}
```

配置按 [OpenAI 官方插件文档](https://developers.openai.com/plugins/build/plugins) 操作。
已有 marketplace 应合并条目，由使用者选择安装；构建脚本不修改宿主配置。
正式版本进入市场后，Codex CLI 可添加 `Lanbasara/zhixing-marketplace`。

## DeepSeek Harness

适配目标从 DSH 0.2.1-rc.5 起，范围由包的 engines.dsh 声明；实际宿主版本
变化后需要重新验证加载。DSH 在当前 profile 中启用 bundle，并注入 skills 服务。
调用例子为 `/zhixing-align`、`/zhixing-implement`，前缀只由注册器添加一次。

正式版本发布后，CLI 安装命令的 TAG 替换为实际已发布标签：

```sh
dsh plugin --profile web add 'git+https://github.com/Lanbasara/zhixing.git#TAG&path:/plugin'
```

Desktop 可在插件市场添加索引源：
`https://raw.githubusercontent.com/Lanbasara/zhixing-marketplace/main/dsh/index.json`。
市场索引在源 Release 成功后独立更新，安装来源固定到对应版本的提交。

## 升级与验收

0.3.3 改进 `setup` 对已有项目的接入判断：沿用现有开发约定，只讨论影响后续
协作的未决选择；已有基础足够时无需修改文件。技能调用名和安装方式不变。

0.3.0 新增 `handoff`，可显式调用或按需组合，用于准备跨会话接续材料。
升级后可选择该技能；原有技能调用名和安装布局保持兼容。

0.2.0 重命名技能并改变安装根目录。移除旧源码包的安装项，再通过所用宿主
安装完整新包，避免同一技能同时来自两份安装。重载后在新会话核对：
16 个技能均可由人选择；6 个人工入口不出现在模型自动调用目录；引用的
原则、共同约定和验证示例可读取。宿主安装、自动选择和模型行为应分别记录证据。
