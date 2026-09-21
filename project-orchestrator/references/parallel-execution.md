# Parallel Execution

多 agent 的目的不是“同时开更多窗口”，而是缩短真正独立的关键路径。

## 1. 哪些任务可以并行

同时满足时再并行：

- 没有未解决的前置依赖。
- 输入已经稳定。
- 输出可以独立验收。
- 不写同一个 working tree。
- 不写同一个可变结果目录。
- 一个任务失败不会让另一个任务的验收标准失效。

如果两个 agent 都需要持续修改同一个核心文件，优先串行或先拆接口，不要用 Git 冲突充当协作机制。

## 2. 标准隔离单元

推荐：

**1 issue = 1 branch = 1 worktree = 1 session = 1 work packet**

示例命名：

- issue: PRJ-31
- branch: PRJ-31-sam-eval
- worktree: ../worktrees/PRJ-31-sam-eval
- tmux/session: prj-31
- output: runs/PRJ-31/

session 名只是便利工具，不能用它判断任务是否存在或是否完成。

## 3. A/B/C 多路线研究

当目标是比较多个方法时：

1. 建一个共同父 issue，写清共同评测协议和最终 gate。
2. A/B/C 分成三个独立 issue。
3. 三路必须尽可能共享同一数据切分、指标和基线口径。
4. 每路可以有自己的内部实现，但不能悄悄改变公共评测标准。
5. 最终 Integration / GOLD issue 只消费已经验证过的 A/B/C 证据。

如果 A/B/C 都还没跑稳，不要提前把最终融合 issue 拆到很细。

## 4. 共享数据和输出

共享只读数据可以被多个 worktree 使用。

可变输出必须隔离，优先：
- runs/<ISSUE-ID>/
- artifacts/<ISSUE-ID>/
- logs/<ISSUE-ID>/

不要让三个 agent 都写 runs/latest/ 或同一个 results.json。

大型数据不复制到每个 worktree。用稳定只读路径或显式配置引用。

## 5. Agent work packet

每个 agent 启动前都收到完整 work packet，至少包含：

- issue ID；
- branch/worktree；
- objective；
- known facts；
- scope；
- do-not-change；
- acceptance criteria；
- verification commands；
- expected artifacts；
- how to report blockers。

禁止只发一句“继续优化方案 B”。这种 prompt 会把项目管理权偷偷交给执行 agent。

## 6. Agent 可以自主到什么程度

可以自主：
- 阅读代码；
- 选择实现细节；
- 调试；
- 在 scope 内迭代；
- 根据失败证据修正实现；
- 补充必要测试。

不能自主：
- 改变项目目标；
- 改公共评测集来让结果变好；
- 删除失败证据；
- 改其他 workstream 的 scope；
- 擅自合并到 main；
- 把未验证结果标成 Done。

遇到这些情况，返回主编排层。

## 7. 主编排层的并行循环

主编排 agent 不应在启动 agent 后“消失”。

循环：

1. 启动可并行 issue。
2. 记录每个 issue 的 branch/worktree/session。
3. 定期读取真实输出/状态，而不只看 agent 文本。
4. 某一路先产出决定性证据时，评估是否影响其他路线。
5. 只有依赖关系真的变化时才重排 Linear。
6. 各路完成后独立验收。
7. 进入 Integration / Decision gate。

## 8. 合并策略

通过验收的分支才进入 PR/merge。

研究路线失败也可以保留 branch/commit 作为证据，但不要求合到产品主线。可以只合：
- 通用工具；
- 可复现实验配置；
- 总结文档；
- 对后续有价值的测试。

不要为了“所有分支都合进去”把互相排斥的实验实现塞进主线。

## 9. 防止 agent 互相覆盖

每次并行前检查：
- git worktree list；
- branch 是否唯一；
- 输出目录是否唯一；
- GPU / 端口 / 锁资源是否冲突；
- 是否共享会被修改的环境配置。

对于 GPU 任务，把设备分配写进 work packet；不要让多个 agent 默认抢 GPU 0。

## 10. 并行结束后的收口

每路都要留下：
- 最终 commit 或明确的 no-code result；
- 验证命令/结果；
- 关键产物路径；
- 一句话结论与限制；
- Linear 状态。

然后再做跨路线比较。不要把不同数据、不同阈值、不同评测版本的数字直接并排当作公平比较。
