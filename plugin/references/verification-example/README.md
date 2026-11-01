# 一个可复跑的验证示例

这个例子展示[共用验证约定](../verification.md)怎样落到可执行方法。
它的对象是一条很小的承诺：用户保存新笔记后，新进程仍能读到准确内容，
原有笔记也保持不变。它是教学资源，不是通用测试框架或生产笔记产品。

[notes.py](notes.py) 是被测 CLI，[verify.py](verify.py) 是独立驱动。
两者只用 Python 3.8 或更新版本的标准库，不需要安装依赖或启动服务。驱动不导入 CLI，
不直接写入其数据文件；预期内容由验证场景给出。

## 复跑

以下命令从仓库根目录执行。也可以从任意目录用脚本的绝对路径执行；
驱动通过自己的文件位置找到默认 CLI，所有子进程在本次独占的临时目录运行。

```sh
python3 references/verification-example/notes.py --help
python3 references/verification-example/notes.py --store unused put --help
python3 references/verification-example/verify.py --help
python3 references/verification-example/verify.py --evidence ../verification-example-evidence/normal
```

把 `--evidence` 换成自己选定的、仓库外尚不存在的目录。驱动拒绝覆盖现有
目录；再次运行应选新目录。成功返回 `0`，行为或运行失败返回 `1`，参数或
证据目录不满足条件返回 `2`。标准输出给出结果和 `report.json` 的位置。

## 这条路径证明什么

| 动作与观察 | 用途 |
| --- | --- |
| 记录 CLI 文件摘要、解释器与环境，通过 `--version` 核对公开身份 | 将观察绑定到实际运行的程序 |
| 用 `init --id` 创建独占数据文件，再由 `status` 和 `list` 读取 | 核对数据身份、格式、空初态及读入口可用 |
| 用 `put` 保存原有笔记，再由新进程读取 | 建立目标场景，并确认写入前提实际可用 |
| 用 `put` 保存新笔记，由另一个进程 `list` | 与独立预期比较，识别未持久化、内容变形或旧数据丢失 |
| 检查数据身份、临时目录文件清单和写入前后的文件摘要 | 观察预期存储副作用，确认读取没有改变已存内容 |
| 退出临时目录上下文，再写出报告 | 只回收本次创建的运行资源，保留清理后仍可读的证据 |

报告保留实际命令、退出码、标准输出与错误、逐项比较、存储摘要和清理结果。
单条命令超过 10 秒时，驱动结束并回收该子进程，保留已捕获的输出与超时标记；
没有正常退出结果的命令，其退出码记为 `null`。失败也写报告，并保留首先失败的判断。
临时数据本身会被删除；需要解释失败的
输入与 CLI 输出仍在报告里。它没有访问其他项目实例，也没有连接外部系统。

## 用反例检查验证是否有区分力

可以复制 `notes.py` 到仓库外，保留 `put` 的成功响应，但让名称为 `added`
的笔记跳过写盘。下面的脚本只创建一个新副本，不修改原程序；目标已存在会失败。

```sh
python3 - <<'PY'
from pathlib import Path

source = Path("references/verification-example/notes.py")
target = Path("../verification-example-evidence/notes-with-lost-write.py")
code = source.read_text(encoding="utf-8")
line = '                args.store.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")'
assert code.count(line) == 1
target.parent.mkdir(parents=True, exist_ok=True)
with target.open("x", encoding="utf-8") as stream:
    stream.write(code.replace(line, '                if args.name != "added":\n    ' + line))
PY
python3 references/verification-example/verify.py --program ../verification-example-evidence/notes-with-lost-write.py --evidence ../verification-example-evidence/lost-write
```

预期退出码是 `1`。报告中 `new save acknowledged` 仍通过，而
`new process reads both exact notes` 失败；实际结果只有原有笔记。
同一验证入口识别了目标缺陷，没有降低预期或把缺陷模式内置成成功场景。
运行报告和故障副本都由调用者保留，确认不再需要后自行删除。

## 边界

这里的版本名是教学程序的固定身份，文件摘要区分不同实现；它不是发布签名。
本例按顺序运行多个进程，未验证并发、崩溃一致性、权限故障、
大数据量或其他产品入口。目录快照只观察本次工作目录内的副作用。
它证明这条窄路径及验证器对所示缺陷的识别能力，不能代替目标项目的验收依据。
