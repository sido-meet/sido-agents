# sido-agents

个人 Agent 组合库，按场景逐步积累。每个顶层组合目录独立维护自己的角色、配置清单、协作流程与说明，类似 sido-skills 中每个 skill 一个目录。

## 组合目录

| 组合 | 用途 | 成员 |
| --- | --- | --- |
| [strict-dev-team](strict-dev-team/README.md) | 严格分工的软件开发、测试与审查 | developer、tester、reviewer |

```text
sido-agents/
├── README.md                  全库索引
├── strict-dev-team/           第一套 Agent 组合
│   ├── README.md              组合用途与使用方法
│   ├── catalog.json           该组合的角色清单
│   ├── agents/engineering/    角色正文
│   ├── workflows/             组合协作流程（可选）
│   └── archive/               来源归档
├── templates/                 通用编写模板
├── scripts/                   共用导出与安装工具
├── tests/                     工具验证
└── dist/<组合>/<harness>/      生成结果
```

以后可以并列增加 `research-team/`、`data-analysis-team/` 等组合（这里只是命名示例，尚未创建）。单角色场景也可以作为只有一个成员的组合保存。

## 使用

需要 Python 3.11+，无第三方运行依赖。以下命令在仓库根目录执行：

```powershell
cd E:\Projects\sido-agents
python scripts/agents.py list
python scripts/agents.py list --bundle strict-dev-team
python scripts/agents.py build --bundle strict-dev-team
python scripts/agents.py install --bundle strict-dev-team --harness codex --project E:\Projects\your-project --dry-run
```

将目标路径换成实际项目，去掉 `--dry-run` 后安装。`--harness` 可选 claude、codex、workbuddy、codebuddy；build 默认导出全部格式，install 必须指定一种。可用 `--agents reviewer` 只选择组合中的一个角色。

导出和安装必须显式指定 `--bundle`，不会因为仓库新增了组合而把所有角色安装进项目。目标文件不同则拒绝覆盖，相同内容可重复安装。

安装后的角色名携带组合前缀，例如 `strict-dev-team-reviewer`。不同组合可以各自定义 reviewer，并安装到同一项目；角色引用和工作流路径一起转换。只安装单个角色不会自动补装其提及的其他角色，需要完整团队时安装整个组合。

## 增加组合

1. 新建顶层 `<组合名>/`，使用小写字母、数字、短横线，以字母开头。
2. 添加 README.md、catalog.json 和 agents/ 中的角色正文；可参考 strict-dev-team，正文模板见 `templates/agent.md`。
3. catalog.json 采用 schema_version 1 和 agents 数组；每条包含 name、scenario、description、prompt、access。prompt 相对于组合目录，必须指向 agents/ 内文件；access 为 read 或 write。
4. 如需协作流程，放入该组合的 workflows/*.md；安装到 `.sido-agents/<组合名>/workflows/`。正文引用使用 `.sido-agents/workflows/<文件名>.md`，导出时补入组合名。
5. `python scripts/agents.py build --bundle <组合名>`；在目标 harness 实际调用验证。

角色名只需在组合内部唯一。源文件正文中的角色短名会在导出时转换成带组合前缀的名称；避免把短名用作与角色无关的代码标识符。组合可以引用已经安装的 skill；技能方法继续放在 sido-skills 中维护。

组合内容与 harness 的适配逻辑分离。现有 harness 格式说明及官方参考见 [strict-dev-team 文档](strict-dev-team/README.md)。新结构已做静态导出与安装测试，未进行真实模型调用验证。
