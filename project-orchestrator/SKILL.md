---
name: project-orchestrator
description: 在主编排 agent、远程开发机、GitHub、Linear、Notion 之间管理一个长期研发项目，并让这些系统始终表达同一个项目状态。适用于“接管/初始化/继续/梳理一个项目”“检查服务器、GitHub、Linear、Notion 是否一致”“让多个 agent 并行推进”“把当前项目工作流复用到新项目”“项目做到哪了、下一步怎么推进”等跨系统项目工作。核心分工：主交互 agent 是控制面；远程开发机是执行面；GitHub 是代码、配置和工程证据真相源；Linear 是任务、依赖和执行状态真相源；Notion 是长期知识、决策和项目叙事真相源。不要用于只改一小段代码、只执行一个命令、只查一个 issue 或只写一页 Notion 的孤立任务，除非用户同时要求同步整个项目状态。
compatibility: 需要至少一种可访问项目代码/远程环境的工具；GitHub、Linear、Notion 连接器按项目实际情况使用。允许部分系统暂时不可用，但必须把未验证状态显式标出。绝不把密码、token、私钥等秘密写入项目上下文。
---

# Project Orchestrator

这个 skill 的目的不是“多用几个工具”，而是让一个项目只有一个逻辑状态。

主编排 agent 负责理解目标、拆任务、调度、核验和同步；远程开发机负责真正执行代码和实验；GitHub、Linear、Notion 分别维护自己最擅长的那一种真相。不要让四个地方各自长出一套项目管理。

## 系统分工

| 系统 | 唯一职责 | 应该放什么 | 不应该放什么 |
|---|---|---|---|
| 主编排 agent | 控制面 | 目标理解、跨系统推理、任务调度、冲突处理、状态汇总 | 把聊天记忆当永久真相源 |
| Remote / SSH / Desktop | 执行面 | 工作树、数据、运行进程、tmux、实验产物、临时日志、agent 执行 | 长期任务状态、最终知识库 |
| GitHub | 工程真相源 | 代码、配置、README、branch、commit、PR、CI、可复现的小型结果摘要 | 大型原始数据、仅存在远程机的临时输出 |
| Linear | 工作真相源 | milestone、issue、父子关系、依赖、优先级、状态、验收标准 | 大段技术笔记、完整实验日志、代码实现细节 |
| Notion | 知识真相源 | 项目 charter、关键决策、阶段结论、长期有效的研究笔记、复盘 | 实时任务看板、每次 commit 的流水账 |

原则：**一个事实只选一个主维护位置，其他地方只链接，不复制维护。**

更详细的冲突处理和完成定义见 references/state-model.md。

## 十条硬规则

1. **先读状态，再改状态。** 接管或恢复项目时，先检查远程工作树、GitHub、Linear、Notion，再决定下一步。
2. **聊天不是数据库。** 重要状态必须落到 GitHub / Linear / Notion 中对应的位置。
3. **远程 dirty working tree 只是暂态。** 未 commit / 未 push 的代码不能当成已经同步的工程状态。
4. **Agent 说“完成”不等于完成。** 必须读取实际输出、执行验证命令，并检查 commit/PR 或结果文件。
5. **Linear issue 是执行单元。** 一个独立任务尽量对应一个 issue；复杂任务再拆子 issue。
6. **近期细、远期粗。** 当前 milestone 可以拆清楚，未来 milestone 只保留目标和 gate；不要在证据不足时提前设计几十个细任务。
7. **并行任务必须隔离。** 一个独立任务对应一个 branch/worktree 和一个执行会话，禁止多个 agent 在同一个 working tree 里同时改。
8. **执行完必须闭环同步。** Remote 结果 → GitHub 工程证据 → Linear 状态 → 必要时 Notion 长期结论。
9. **失败也要成为状态。** 跑失败、假设被证伪、路线暂时放弃，都要留下可追溯证据，不能只保留成功路径。
10. **秘密永不落盘到公共项目管理。** token、密码、私钥、cookie 等不得写进 GitHub、Linear、Notion 或项目上下文模板。

## 工作流

### 0. 先判断当前模式

常见模式只有五类：

- **Bootstrap**：新项目第一次建立这一套工作流。
- **Resume**：项目已经存在，从中断处继续。
- **Reconcile**：怀疑远程、GitHub、Linear、Notion 状态不一致。
- **Execute**：已经知道要做什么，开始推进一个或多个 issue。
- **Handoff / Review**：阶段结束，整理证据、同步状态和下一步。

不要一上来就建 issue 或运行 agent。先判断是哪一种模式。

### 1. 建立项目坐标

优先寻找项目根目录下的 .project/orchestration.yaml。不存在时：

1. 从当前环境、仓库、Linear、Notion 和用户输入中尽量自动推断。
2. 仍未知的字段保持 null，不要编造。
3. 在用户要求初始化/固化工作流时，从 assets/project-context.template.yaml 生成 .project/orchestration.yaml。
4. 只保存稳定、非秘密的坐标：repo、远程路径、Linear project、Notion hub、命名规则等。

这个文件的作用是让新会话、新 agent、新机器都知道“这个项目的四个坐标在哪里”，而不是保存动态任务状态。

### 2. 接管项目时做一次状态对账

至少检查：

**Remote**
- 当前项目路径是否正确。
- git status、当前 branch、HEAD。
- 是否有未提交/未跟踪文件。
- 是否有正在运行的 tmux / agent / 训练或实验进程。
- 关键输出目录和最近更新时间。

**GitHub**
- default branch 最新 commit。
- 活跃 branch / PR。
- 当前任务对应的 commit 是否已经 push。
- CI / review 是否阻塞。

**Linear**
- 当前 project / milestone。
- In Progress、Blocked、Todo 的 issue。
- issue 父子关系和依赖是否符合真实执行顺序。
- “Done” issue 是否真的满足验收条件。

**Notion**
- 项目首页/charter 是否仍反映当前目标。
- 最近关键决策、结论、限制有没有遗漏。
- 是否把旧方案写成了当前方案。

输出一张简短状态矩阵：

| 域 | 当前状态 | 证据 | 是否一致 | 下一动作 |
|---|---|---|---|---|

如果发现冲突，按 references/state-model.md 的领域真相源处理，不做“多数投票”。

### 3. 用 Linear 表达计划，而不是复制实现

推荐层级：

**Project → Milestone → Issue → Sub-issue（仅在需要时）**

规划遵循 progressive elaboration：

- 当前阶段：目标、验收标准、依赖、可执行 issue 拆清楚。
- 下一阶段：只到 workstream / gate。
- 更远阶段：只保留方向和进入条件。

如果有 A/B/C 多路线探索：

- A、B、C 各自成为独立 workstream。
- 每条路线有自己的验证目标和退出条件。
- 最后增加一个 Integration / GOLD / Decision gate。
- **只有当各路线证据足够时，才细化最终融合方案。**

不要因为 Linear 能建层级就提前把未来做成一棵巨大的任务树。

### 4. 每个 issue 生成一个 work packet

启动远程 agent 前，把 Linear issue 转成一个明确执行包。优先使用 assets/work-packet.template.md，至少包含：

- issue ID 与目标；
- 为什么做；
- 输入与已知事实；
- 允许修改的范围；
- 禁止改动的范围；
- 验收标准；
- 必须执行的验证；
- branch / worktree；
- 预期产物；
- 完成后需要回传的证据。

默认 branch 名：

**<ISSUE-ID>-<short-slug>**

如果项目已经有明确命名规范，遵守项目规范。

Agent 可以优化“怎么做”，不能自行改变“为什么做”和验收标准。发现目标本身有问题时，应返回证据给主编排 agent，由主编排层决定是否改 issue。

### 5. 远程执行与多 agent 并行

主编排 agent 负责调度，远程 agent 负责执行。

可以并行的前提：

- 任务之间没有未解决的依赖。
- 不会修改同一个 working tree。
- 不会竞争同一份可变输出文件。
- 各自成功/失败都能独立验收。

推荐隔离：

**1 Linear issue = 1 Git branch = 1 worktree = 1 tmux/session = 1 work packet**

详细规则见 references/parallel-execution.md。

tmux 只是进程容器，不是真相源。session 名丢了不等于任务丢了；最终状态仍由文件、commit、PR 和 Linear 决定。

### 6. 验证：不接受“agent 自报成功”

每个任务至少完成三类核验：

1. **产物核验**：目标文件/结果是否真的存在、时间和路径是否正确。
2. **行为核验**：测试、评测、检查命令是否通过。
3. **版本核验**：git diff、commit、push/PR 是否与目标一致。

研究/实验类任务还要检查：

- 输入数据和参数是否与 issue 约定一致。
- 指标分母和评测集是否正确。
- 失败条件有没有被隐藏。
- 结果是否足够支持结论。

验证失败就继续保持 In Progress / Blocked，不要因为代码已经写完就标 Done。

### 7. 按固定顺序同步

任务通过验收后，默认按这个顺序收口：

**Remote → GitHub → Linear → Notion → 用户汇总**

具体是：

1. Remote：确认 working tree 和结果完整。
2. GitHub：commit / push / PR；工程状态先落地。
3. Linear：附上 commit/PR/结果证据，更新 status。
4. Notion：只有产生长期有效的决策、结论、边界或复盘时才更新；不要抄 Linear 流水账。
5. 主编排 agent：给用户一个当前状态快照和下一批可执行任务。

对于纯研究、纯决策、纯文档任务，按 references/state-model.md 使用对应的 Done 定义，不强求 PR。

### 8. 系统不可用时降级，而不是猜

- Remote 不可用：不能宣称执行结果已验证。
- GitHub 不可用：可以继续本地实验，但工程同步标记 Pending。
- Linear 不可用：已有清晰 scope 时可以执行，但任务状态标记 Pending Sync。
- Notion 不可用：通常不阻塞代码/实验，只延后长期知识沉淀。
- 某个系统没有 connector：不要伪造它的状态；显式写 Unverified / Pending Sync。

恢复连接后优先执行 Reconcile，而不是直接继续下一任务。

## 给用户的默认汇报格式

不要把工具调用流水账倾倒给用户。默认只给四块：

**当前状态**：项目在哪个 milestone / 哪几个 issue 正在推进。  
**刚完成**：结果 + 核验证据 + commit/PR。  
**阻塞/冲突**：哪些系统不一致、缺什么证据。  
**下一步**：可以立即执行的 issue，哪些可以并行。

当用户问“所有系统是否一致”时，再展开完整状态矩阵。

## 按需读取

| 情况 | 读取 |
|---|---|
| 状态冲突、Done 定义、四个系统谁说了算 | references/state-model.md |
| 多 agent、A/B/C 并行、branch/worktree/tmux 隔离 | references/parallel-execution.md |
| 新项目初始化项目坐标 | assets/project-context.template.yaml |
| 给远程 Claude/Codex/其他 agent 下任务 | assets/work-packet.template.md |

## 完成标准

一次跨系统项目操作只有在以下条件满足时才算闭环：

- 当前目标与 issue scope 清楚。
- Remote 实际状态被检查。
- 代码/配置变更有 GitHub 工程证据，或明确说明任务不需要 GitHub 变更。
- Linear 状态与真实完成度一致。
- 长期有效的决策/结论已经进入 Notion，或明确判断无需更新。
- 未同步/未验证内容被显式标出。
- 用户能从最终汇报看懂“现在在哪、刚发生了什么、下一步是什么”。
