---
name: zhixing-release
description: 准备、发布或接续知行插件的 GitHub Release 与三端市场交付；普通开发和提交 PR 不触发发布。
---

# 发布知行

本技能只供知行源码仓维护者使用。读取仓库根目录的
[RELEASING.md](../../../RELEASING.md)，以其中的交付边界为准。
先通过 git remote 和 gh 确认正在操作 Lanbasara/zhixing 与
Lanbasara/zhixing-marketplace；不操作其他产品或使用者的全局安装。

发布请求先形成可核验的具体对象：版本、源码 main commit、候选运行及摘要、
必需检查、实际宿主验收范围、市场 main commit，以及要执行的外部动作。
在只读预检和候选验证完成后，检查用户授权是否覆盖这些对象；缺少授权时
只集中确认尚未授权的发布范围，已有明确授权不重复索取。
普通开发授权不自动授权创建发行版或把未合并源码当作正式版本。

使用 gh 检查远端 main 与 tag 保护、source-release reviewer 及不可变 Release
设置实际生效。未合入 main 的代码通过普通 PR 合入，不跳过必需检查。
运行预览并用 scripts/release.py 的 --verify 从精确 Git 对象核对下载物。
已授权后按 RELEASING 的顺序推进 tag、受保护环境、Release，再处理市场 PR。
每次选择工作流运行和 artifact 都匹配源提交、事件与 tag，不能只选择“最新”。

批准 source-release 前再次验证 annotated tag 的远端对象与目标提交，核对
当前运行的正式 artifact。正式 Release 成功后才使用同一运行的市场候选；
对照记录的市场基线重建四个索引文件，并按市场仓正常 PR 保护提交。
维护者可以代为执行已授权的环境批准和市场 PR 合并，不需要逐次等待继续。

失败时交付实际停在哪一阶段及恢复条件。已经创建的 tag 和 Release 保持不变；
市场更新失败可从同一发行版恢复。版本、提交、市场基线或授权范围变化时，
重新预检受影响部分，不能用强推、删标签、改旧 Release 或关闭保护来继续。
完成后给出 Release、工作流、市场 PR 和实际验证范围，并清理自己创建且已无用途的资源。
