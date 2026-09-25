# strict-dev-team

严格开发协作组合：developer + tester + reviewer。作为 sido-agents 中一个独立命名的组合维护。

面向不同场景的个人 Agent 定义库。一份角色正文，按 harness 导出配置。

首批角色来自 `E:\Projects\sido-resume\materials\projects\movie_agent\.codebuddy\agents`。可以复用的是职责、边界、工作步骤和输出协议；工具权限、模型选项与加载方式需要分别适配。

## 当前内容

| 场景 | Agent | 职责 |
| --- | --- | --- |
| engineering | developer | 生产代码实现和缺陷修复 |
| engineering | tester | 测试设计、执行和失败分析 |
| engineering | reviewer | 只读审查，按严重程度和责任方报告问题 |

```text
agents/<scenario>/*.md      通用角色正文，主要维护入口
catalog.json               名称、场景、描述、读写意图与正文路径
workflows/                 可选的跨角色协作流程
../templates/agent.md      新场景角色模板
../scripts/agents.py       导出和项目安装工具（Python 3.11+，无第三方依赖）
../dist/strict-dev-team/<harness>/            生成结果，不手工修改，不纳入 Git
archive/movie-agent/       原始三个 agent 和工作流的逐字节副本
../tests/                  导出和安装边界验证
```

## 快速使用

在 PowerShell 中执行：

```powershell
cd E:\Projects\sido-agents
python scripts/agents.py list --bundle strict-dev-team
python scripts/agents.py build --bundle strict-dev-team
```

输出包含 Claude Code、Codex、WorkBuddy 和 CodeBuddy 四份配置。WorkBuddy 与 CodeBuddy 共用同一适配格式。

项目级安装示例（将目标路径替换为你的实际项目）：

```powershell
python scripts/agents.py install --bundle strict-dev-team --harness claude --project E:\Projects\your-project --dry-run
python scripts/agents.py install --bundle strict-dev-team --harness claude --project E:\Projects\your-project
python scripts/agents.py install --bundle strict-dev-team --harness codex --project E:\Projects\your-project
python scripts/agents.py install --bundle strict-dev-team --harness workbuddy --project E:\Projects\your-project
```

安装名自动加 `strict-dev-team-` 前缀，避免与其他组合中的同名角色冲突。正文中的角色引用与工作流路径同步转换。`--agents` 仍使用组合内部的短名称。

只安装某些角色：

```powershell
python scripts/agents.py install --bundle strict-dev-team --harness codex --agents reviewer --project E:\Projects\your-project --dry-run
```

安装前会检查所有目标文件；存在不同内容的同名文件时，整次安装拒绝写入，请先对比并手工合并。相同内容可重复安装。升级已有角色时也遵守此规则。安装不会修改项目的 AGENTS.md、CLAUDE.md、CODEBUDDY.md 或 config.toml。`build` 可以覆盖生成目录中的文件；缩小角色选择不会清理旧导出，精确选择应使用 `install --agents`。

本库的创建仅生成库和导出结果，没有向任何既有项目或用户级配置安装角色。

## Harness 适配

| Harness | 项目安装位置 | 格式 |
| --- | --- | --- |
| Claude Code | `.claude/agents/*.md` | YAML frontmatter + Markdown |
| Codex | `.codex/agents/*.toml` | name、description、developer_instructions |
| WorkBuddy / CodeBuddy | `.codebuddy/agents/*.md` | YAML frontmatter + Markdown |

不固定模型和 reasoning effort，继承运行环境选择。原文件的 `effort: high` 留在归档中。Claude 与 CodeBuddy 的 reviewer 仅列出 Read/Grep/Glob；Codex reviewer 声明 `sandbox_mode = "read-only"`。这些配置不等价于完全相同的工具权限：Codex 的实时父会话权限覆盖可能优先于角色默认值，外部工具权限也需由宿主控制。developer/tester 的文件归属仍是提示词约束，不是目录级沙盒。

格式依据 2026-09-26 查阅的官方文档：

- [Claude Code subagents](https://code.claude.com/docs/en/sub-agents)
- [Codex custom agents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [WorkBuddy 项目配置](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Project)
- [CodeBuddy 目录与 agent 文件格式](https://cloud.tencent.com/document/product/1831/137016)

这里的 Claude 指 Claude Code。这里只支持 Codex 文档中的 standalone agent TOML 格式；旧版本如果只支持 `[agents.<name>]` 注册，需要升级或另做 legacy 适配。安装后在目标 harness 新会话中请求调用对应角色，确认被实际发现。已验证导出和安装逻辑；尚未在三个 harness 中分别进行真实模型调用，不能把静态检查当作运行时兼容性认证。

## 独立调用与严格协作

独立使用示例：

> 请调用 strict-dev-team-reviewer，审查当前修改是否满足需求。提供实际代码快照、问题位置和证据，不修改文件。

完整流程示例：

> 请读取项目根目录 `.sido-agents/strict-dev-team/workflows/strict-development.md`，启用该严格开发流程。主会话负责协调，分别调用 strict-dev-team-developer、strict-dev-team-tester 和 strict-dev-team-reviewer；给各角色提供工作流内容、需求、文件边界和快照标识。

工作流随安装复制到 `.sido-agents/strict-dev-team/workflows/strict-development.md`，不会自动注入宿主全局规则。没有明确启用时，不强制启动整个团队。主会话负责实际调度，定义文件本身不会自动形成团队。没有子 Agent 能力时需说明限制，不能用同一轮自审假装独立审查。

原规则的分工、测试后审查、修复同步点、revision 一致性和最多两轮审查保留在可选工作流中。通用角色移除了对原项目规则的硬依赖，把 LangGraph 配置名泛化；测试/审查增加 BLOCKED 状态；未提交修改必须纳入快照，不能只用 HEAD 表示实际版本。

## 扩展本组合

1. 在 `strict-dev-team/agents/<scenario>/` 下按 `templates/agent.md` 新建正文，例如 `agents/research/literature-reader.md`。
2. 在 `strict-dev-team/catalog.json` 增加条目；name 在组合内部唯一，使用小写字母、数字和短横线，access 为 read 或 write。
3. 运行 `python scripts/agents.py build --bundle strict-dev-team` 与 `python -m unittest discover -s tests`。
4. 在目标项目安装，实际调用并检查行为和权限。

Agent 描述“由谁负责、输入输出和边界”；Skill 保存某项工作的具体方法与配套资源。你已有的 `sido-skills` 可以继续独立维护；只有目标 harness 已安装相应 skill 时，角色才应引用它。项目目录、命令、业务背景放在目标项目约定中，避免进入通用角色正文。

原导出保留在 `legacy-dist/`，仅供迁移对比，不再更新；新导出位于仓库根目录 `dist/strict-dev-team/`。本次没有修改外部项目已安装的定义。
