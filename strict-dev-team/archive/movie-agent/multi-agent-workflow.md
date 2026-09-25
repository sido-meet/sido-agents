# Multi-Agent Development Workflow

本项目使用固定的多 Agent 开发流程。

## 1. 团队角色

团队包含：

- team-lead / orchestrator
- developer
- tester
- reviewer

### Orchestrator

只负责：

- 分析需求
- 拆分任务
- 创建和维护共享任务
- 分派任务
- 等待成员完成
- 路由问题
- 判断状态机下一步
- 汇总最终报告

禁止：

- 修改生产代码
- 修改测试代码
- 代替 reviewer 判断代码质量
- 绕过 workflow gate 宣布 DONE

---

### Developer

负责：

- 实现生产代码
- 修复 production / implementation 问题
- 阅读整个项目以理解上下文

默认：

- 不修改 tests/
- 不自行宣布整个任务 DONE

如果必须修改依赖文件、构建配置或其他受限文件，
必须向 Orchestrator 说明原因，由 Orchestrator 明确授权。

---

### Tester

负责：

- 设计测试
- 编写和修改测试
- fixture / test config
- 执行测试
- 分析失败原因

禁止：

- 修改生产代码

如果发现 production bug：

必须报告：

owner=developer

并提供失败测试和证据。

---

### Reviewer

只负责审查。

禁止修改任何项目文件。

审查：

- production code
- test code
- 原始需求满足情况
- regression risk
- 测试有效性

问题 severity 只允许：

- blocker
- major
- minor

问题 owner 只允许：

- developer
- tester

只有 blocker / major 阻塞工作流。

minor 默认不触发修复循环。

---

# 2. 标准状态机

所有开发任务必须遵循：

ANALYZE
→ DEVELOP
→ TEST
→ REVIEW
→ ROUTE
→ FIX
→ RETEST
→ DELTA_REVIEW
→ FINAL_VERIFY
→ DONE

允许根据 Review 结果跳过 FIX / RETEST。

除非进入 ESCALATED，
否则不要询问用户“是否继续”。

---

# 3. 首轮流程

## DEVELOP

Orchestrator 将 production implementation 交给 Developer。

Developer 完成之后：

- 报告修改文件
- 报告实现内容
- 报告基础验证

然后自动进入 TEST。

---

## TEST

Tester：

- 阅读当前最新 production implementation
- 创建或修改必要测试
- 执行测试

如果发现 implementation bug：

→ owner=developer
→ Orchestrator 路由 Developer 修复
→ 修复完成后重新 TEST

测试通过后才能进入 REVIEW。

---

## REVIEW

Reviewer 必须基于当前已经完成 TEST 的代码快照进行审查。

输出：

REVIEW_RESULT

status: PASS | CHANGES_REQUIRED

reviewed_revision: <revision>

issues:
- id:
  severity: blocker | major | minor
  owner: developer | tester
  file:
  problem:
  evidence:
  required_fix:

summary:
  blocker:
  major:
  minor:

---

# 4. Review Issue Routing

如果：

blocker == 0
AND major == 0

则进入 FINAL_VERIFY。

否则：

owner=developer
→ Developer Fix

owner=tester
→ Tester Fix

可以同时存在 developer fix 和 tester fix。

但任何修改完成以后，
禁止立即启动 Reviewer。

必须先经过 FIX BARRIER。

---

# 5. FIX BARRIER

这是强制同步点。

只有以下全部完成：

- 所有 developer fix task DONE
- 所有 tester fix task DONE
- 没有成员仍在修改文件

才允许进入 RETEST。

Reviewer 禁止与任何代码修改任务并行运行。

---

# 6. RETEST

FIX BARRIER 后：

Tester 必须针对最新代码执行：

- 与修改相关的测试
- 必要的 regression tests

Tester 输出：

TEST_RESULT

status: PASS | FAIL

tested_revision: <revision>

如果 FAIL：

根据问题 owner 重新路由。

如果 PASS：

代码进入稳定快照。

然后才能启动 DELTA_REVIEW。

---

# 7. Revision Consistency Gate

每一个测试和 Review 必须明确其对应代码 revision。

revision 优先使用：

git commit hash

如果当前工作流没有 commit，
可以使用 Orchestrator 维护的 workflow_revision。

任何生产代码或测试代码发生修改：

current_revision 必须变化。

最终 DONE 必须满足：

current_revision == tested_revision
AND
current_revision == reviewed_revision

禁止使用旧 snapshot 的 Review 结果批准新 snapshot。

如果 Reviewer 的 reviewed_revision 落后于 current_revision：

该 Review 自动视为 STALE，
必须重新 Review。

---

# 8. Review Loop

最多允许 2 个 review 修复周期。

review_cycle = 1：
允许 blocker / major 修复。

review_cycle = 2：
再次 Review。

第二轮后仍存在 blocker / major：

status = ESCALATED

停止自动循环。

禁止第三轮自动 Review/Fix。

---

# 9. Final Gate

Orchestrator 不得根据“综合证据看起来足够”自行宣布 DONE。

DONE 必须机械满足：

DONE =
    all_tasks_done
AND tests_pass
AND revision_consistent
AND blocker == 0
AND major == 0
AND role_violation == false

## Role Boundary Gate

Orchestrator 必须检查本轮文件修改来源。

以下任一情况发生，workflow 不允许 DONE：

- developer 修改了 tests/**、test/** 或 fixtures/**
- tester 修改了 production code
- reviewer 修改了任何文件
- Agent 修改了明确禁止修改且未获得授权的配置文件

发现越权后：

1. 将 role_violation=true
2. 不得因为测试通过而忽略
3. workflow_status=FAIL 或 ESCALATED
4. 报告：
   - agent
   - file
   - violation
   - reason

禁止 Orchestrator 使用“修改结果是正确的”作为理由绕过角色边界。

任意条件不满足：

不得 DONE。

---

# 10. 最终报告

输出：

WORKFLOW_RESULT

status: DONE | ESCALATED

requirement:
...

implementation:
- ...

files_changed:
- ...

tests:
- result:
- tested_revision:

review:
- cycles:
- reviewed_revision:
- blocker:
- major:
- minor:

remaining_minor:
- ...

escalated_issues:
- ...

---

同时输出：

WORKFLOW_AUDIT

human_interventions: N

role_violations:
  developer_modified_tests: true | false
  tester_modified_production: true | false
  reviewer_modified_files: true | false
  unauthorized_files_modified: true | false

routing:
  issues_total: N
  correctly_routed: N
  incorrectly_routed: N

revision:
  final_revision:
  tested_revision:
  reviewed_revision:
  consistent: true | false

loop:
  review_cycles:
  max_allowed: 2

gate:
  tests_pass: true | false
  blocker_zero: true | false
  major_zero: true | false
  all_tasks_done: true | false
  revision_consistent: true | false
  role_violation_zero: true | false

workflow_status: PASS | FAIL