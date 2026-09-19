# 项目总结与复盘模式

这份参考把“实验报告”扩展到项目阶段总结，但保持同一原则：**只总结有来源的事实，不替项目补剧情。**

## 项目阶段总结

最小信息模型：

| 类别 | 问题 |
|---|---|
| Goal | 原来要解决什么？成功标准是什么？ |
| Progress | 这阶段实际做了什么？ |
| Outcome | 已经产生什么可验证结果？ |
| Gap | 距离目标还差什么？ |
| Decisions | 已经做了哪些关键决定？ |
| Risks / Dependencies | 什么可能阻塞或改变结果？ |
| Open Questions | 哪些关键问题还没有证据？ |
| Next Actions | 下一步具体做什么？ |
| Asks | 需要领导/协作者拍板或提供什么？ |

不是每个项目都需要所有栏。没有内容的栏可以省掉，不要填模板废话。

## 产出不等于结果

项目总结最常见的问题是把 activity 当 outcome：

- “完成自动标注脚本”是产出。
- “人工复核时间从 X 降到 Y”才是 outcome。
- 如果还没测 outcome，就写“脚本已完成，效率收益尚未量化”。

这比把所有完成事项写成“取得显著提升”可信。

## Planned vs Actual

有明确计划基线时，优先展示：

| Item | Planned | Actual | Gap | Why it matters |
|---|---|---|---|---|

没有计划基线时不要事后制造一个。

时间、预算、样本规模、指标、覆盖范围都可以比较，但必须使用同一口径。

## Decision / Ask

Executive briefing 里最有价值的部分往往不是“总结”，而是让读者知道是否需要行动。

只有存在真实决策点时才加：

**Decision needed:** 读者要决定什么。  
**Why now:** 为什么现在必须决定。  
**Evidence:** 支撑判断的事实。  
**Trade-off:** 不同选择的代价。  
**Open question:** 哪个未知可能改变决定。

用户没要求推荐时，可以中立展示选项；用户要求建议时，建议必须显式绑定证据和假设。

## Open Questions

资料缺失或相互冲突时，不要用“合理猜测”把洞补上。

把关键未知写成 Open Questions，例如：

- 真实设备上的 false positive 还没有验证。
- 当前结果只覆盖 2.4 GHz，不能外推到 5 GHz。
- 风险 R3 没有明确 owner。
- 这轮优化是否影响延迟尚未复测。

这不是报告“不完整”，而是报告准确表达了当前知识边界。

## 项目复盘 / retrospective

复盘不是找人背锅，而是解释为什么系统在当时会产生这个结果。

推荐结构：

1. Summary / Impact
2. Planned vs Actual
3. Timeline（只有必要时）
4. What worked
5. What didn't
6. Contributing factors
7. Lessons
8. Action items

### What worked 也要写

复盘只记录失败会失去校准信息。那些成功挡住风险、缩短定位时间、提高验证可信度的流程应该保留。

### Root cause 谨慎使用

只有证据支持时才写 root cause。

如果只能确认“相关因素/贡献因素”，就这样写；不要为了复盘格式硬做五个 Why 得出虚假的唯一根因。

## Action items

Action item 最好是：

- Specific：动作具体。
- Owned：来源中有 owner；没有就 TBC。
- Dated：来源中有期限；没有就 TBC。
- Closeable：什么算完成清楚。

推荐字段：

| Action | Owner | Due | Done when | Source/Reason |
|---|---|---|---|---|

不要凭空分配人，不要凭空给日期。

## 项目状态

如果已有明确的 Green/Amber/Red 或其他状态体系，可以沿用。

如果项目没有既定状态规则，不要模型自己“评为 Amber”。用事实描述替代：“核心算法已完成，真实设备验证未开始，交付日期仍取决于数据采集”。

## Recurring reports

周报/月报/持续项目页要注明：

- **As of:** 数据/材料截止时间。
- **Sources scanned:** 这次实际覆盖哪些来源。
- **Changed since last report:** 与上一版相比新增/变化。
- **Gaps:** 哪些来源不可访问或未更新。

这样下一次刷新不会把“没有搜到”误写成“没有发生”。
