# State Model

这个文件定义 project-orchestrator 的“谁说了算”。

## 1. 领域真相源

不要给所有系统排一个总优先级。不同领域有不同 owner。

| 领域 | 主真相源 | 辅助证据 |
|---|---|---|
| 代码、配置、脚本、版本 | GitHub | Remote working tree |
| 当前正在运行什么 | Remote | tmux / process / logs |
| 任务状态、优先级、依赖 | Linear | GitHub PR / Remote evidence |
| 项目目标与长期知识 | Notion | Linear project description / README |
| 实验原始产物 | Remote / 专用存储 | GitHub 中的小型 summary/manifest |
| 工程是否集成 | GitHub default branch / PR state | Linear Done |
| 用户刚刚明确做出的新决定 | 当前用户指令 | 后续同步到 Linear/Notion |

“最新时间戳”不能跨领域自动赢。例如 Notion 页面昨天写了“方案 A”，今天 GitHub 出现方案 B commit，并不代表项目战略已经切到 B；要看 Linear/用户是否做了这个决策。

## 2. 常见冲突怎么处理

### Remote HEAD 比 GitHub 新

含义通常是：存在未 push commit，或本地 branch 没同步。

处理：
1. 检查 git status、log、remote tracking。
2. 验证 commit 是否属于当前 issue。
3. 需要保留则 push/PR；否则保持为未同步状态。
4. 在同步前不要把 GitHub 说成“已经有这版”。

### Linear 已 Done，但 PR 未合并

先判断 issue 类型。

- 代码/工程任务：通常 Linear 状态过早，恢复为 In Progress / Review，直到满足项目的 merge gate。
- 研究任务：如果验收标准只是得到可追溯实验结论，未合并 PR 不一定阻塞 Done。
- 决策任务：以决策记录和相关执行 issue 是否创建为准。

### GitHub 已合并，但 Linear 仍 In Progress

GitHub 证明代码集成，不自动证明 issue 全部验收完成。检查 Linear acceptance criteria。若全部满足，再更新 Done。

### Notion 写的是旧路线

Notion 是长期知识，不是实时执行状态。保留历史记录，但把当前决定、日期、原因和相关 Linear/GitHub 证据补上。不要静默重写历史，让过去看起来从未发生。

### Agent summary 与文件/测试冲突

永远相信可复现证据，不相信自报。summary 只能作为导航，不是验收证据。

## 3. Done 定义按任务类型区分

### 代码 / 工程任务

至少需要：
- acceptance criteria 满足；
- 必要测试/检查通过；
- 变更已 commit；
- 按项目规则 push/PR/merge；
- Linear 附有可追溯证据。

### 实验 / 研究任务

至少需要：
- 输入、配置、数据版本可追溯；
- 实验实际完成，失败也有记录；
- 指标或观察经过核验；
- 结论不强于证据；
- 结果路径/summary 可被后续人找到；
- Linear 更新结果与下一决策。

不要求把大型结果提交 GitHub。

### 决策任务

至少需要：
- 决策问题清楚；
- 关键证据与限制记录；
- 决定了什么、没有决定什么清楚；
- Notion 有长期记录；
- Linear 中产生对应执行任务（如果需要执行）。

### 文档任务

至少需要：
- 文档实际更新；
- 内容与当前工程/任务状态一致；
- 链接可访问；
- 相关 issue 验收通过。

## 4. 状态矩阵

Reconcile 时推荐生成：

| 域 | 期望 | 实际 | 证据 | 差异 | 动作 |
|---|---|---|---|---|---|
| Remote | issue branch | ... | git status / process | ... | ... |
| GitHub | pushed / PR | ... | commit / PR | ... | ... |
| Linear | In Progress | ... | issue | ... | ... |
| Notion | current decision | ... | page | ... | ... |

只列有意义的差异，不为了表格完整而制造信息。

## 5. 最小可追溯链

理想情况下，一个工程任务能顺着这条链追：

**Linear issue → branch/worktree → commit/PR → 验证结果 → Linear closure**

如果产生长期知识，再加：

**→ Notion decision / finding**

Notion 不需要记录每个 commit；GitHub 也不需要复制完整决策长文。互相放链接即可。

## 6. Pending Sync 是合法状态

工具中断时，不要强行伪装成一致。

允许明确记录：
- Pending GitHub Sync
- Pending Linear Sync
- Pending Notion Sync
- Remote Unverified

恢复连接后，先消掉这些债务，再开始新的跨系统任务。
