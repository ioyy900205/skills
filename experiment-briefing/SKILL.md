---
name: experiment-briefing
description: 把实验、评测、分析结果或项目阶段成果做成可追溯的 HTML 汇报页/展示页/dashboard。适用于“实验汇报/结果页/项目阶段总结/项目复盘/技术汇报/给领导看/dashboard/开端口分享”，以及需要在网页里比较配置、展示全条件结果、整理项目进展/风险/决策/下一步、嵌入音频或样例证据、改进已有报告时。即使用户没说 HTML，只要最终交付明显是可浏览、可分享的技术或项目结果页面，也应使用。不要用于最终只需要 Markdown/普通周报文字、幻灯片、Notebook、原始数据分析或论文正文的任务，除非用户同时要求 HTML 汇报页。
compatibility: Python 3；图片内嵌需要 Pillow；浏览器体检需要 Node.js + Playwright；端口分享脚本面向 Linux。
---

# Experiment Briefing

目标只有两个：

1. **领导 30 秒拿到结论、状态和需要关注的事情。**
2. **自己三个月后能追溯每个数字、判断和结论怎么来的。**

前面放结论和行动边界，后面放证据、限制、来源和复现信息。

## 六条硬规则

1. **来源是唯一真相源。** 实验数字从运行目录或结构化汇总读回；项目状态从真实记录/文件/提交/会议或用户输入提取，不凭印象补全。
2. **改生成器，不改生成后的 HTML。** 报告必须能重新生成。
3. **结论不能强于证据。** 阴性结果照写；数据推翻预设叙事时，重写叙事。
4. **缺失就是缺失。** “未运行/未知/TBC”和“运行后为零/明确无进展”不能混在一起。
5. **把未决问题显式化。** 不确定事实、缺失输入、未验证归因放到 Open Questions / Gaps，不替读者猜答案。
6. **限制、来源和复现属于交付。** 关键 caveat 不藏；项目汇报也要注明 as-of 时间与来源范围。

## 工作流

### 1. 先检查现有项目与证据

先看运行目录、已有汇总、报告生成器、README、实验记录、项目约定，以及用户提供的项目材料。优先复用已有统计函数、设计系统和目录结构。

实验只有日志、零散图片或逐样本结果时，先整理结构化 JSON/CSV。项目总结只有散乱材料时，先形成可追溯的事实清单：进展、决策、风险、问题、下一步及各自来源。

不要从截图或记忆人工抄最终数字；不要给未声明的 owner、日期、项目状态。

### 2. 先判断报告模式

最终页面可以是以下一种或混合：

- **实验结果**：重点是方法、全条件结果、失败边界、限制、复现。
- **项目阶段总结 / status**：重点是目标、已完成、计划 vs 实际、关键结果、风险/依赖、决策、下一步和 asks。
- **项目复盘 / retrospective**：重点是时间线、结果、what worked / what didn't、贡献因素、经验和可关闭的 action items。
- **决策汇报 / decision brief**：重点是事实、选项、权衡、风险、未决问题，以及用户明确要求时的建议。

项目类模式按需读取 `references/project-briefing.md`。

默认输出单文件自包含 HTML；大量音频/视频时使用 HTML + assets 相对路径。

如果用户只要文字周报、PPT 或 Notebook，不要强行转成 HTML。

### 3. 从生成器开始

优先从 `assets/report_template.py` 起步，并复用：

- `assets/report_html.py`：HTML、主题、表格和图片内嵌
- `assets/charts.py`：内联 SVG 图表
- 项目已有等价模块：存在时优先用项目版本

实验数字、项目 KPI、进展计数等都从结构化来源计算或提取。正文和图表必须共享同一事实源。

### 4. 第一屏先回答“所以呢”

实验结果默认：

**Hero → 方法 → 主结果 → 全条件证据 → 边界归因 → 口径与限制 → 复现**

项目阶段总结默认：

**Hero → 目标与当前状态 → 本阶段完成 → 关键结果/证据 → 风险与依赖 → 决策/未决问题 → 下一步/Asks → 来源**

复盘默认：

**Hero → 计划与实际 → 时间线 → 结果 → What worked / What didn't → 贡献因素 → Lessons → Actions**

标题写结论/状态，不写“XX 项目汇报”。

第一屏通常只需要 3–4 个最有信息量的 KPI 或状态块。不要为了“像 dashboard”而填满卡片。

如果领导需要做决定，第一屏或靠前位置增加 **Decision / Ask**；没有明确需要拍板的事情就不要硬造。

更详细的页面结构见 `references/report-structure.md`。

### 5. 把事实、解释、行动分开

遇到归因、消融、误差分解、失败原因时读取 `references/evidence-and-claims.md`。

项目总结额外遵守：

- **事实**：已经发生、可定位来源。
- **解释**：对事实的归纳或原因判断，要标明证据强度。
- **风险/问题**：尚未发生或尚未解决的暴露。
- **行动**：明确动作；owner、due date、definition of done 只有来源里存在时才写，未知就写 TBC。
- **Open Questions**：会改变结论或下一步，但当前资料无法回答的问题。

不要把“观察到相关”写成“根因”；不要把若干独立消融横向相加成总归因。

### 6. 分享前先做分析 QA

对关键数字和关键结论执行 `references/analysis-validation.md`：

- 问题是否答对。
- 指标、分母、时间窗、比较基线是否一致。
- 是否有缺失、重复、未跑条件、partial period。
- 子项是否该加总；平均数是否被错误再平均。
- 图和标题是否可能让快速阅读者得出错误结论。
- 结论是否遗漏合理的替代解释。

发现 blocking issue 时先修再生成最终版本；不能修时把它写进限制和 Open Questions。

### 7. 验证页面本身

生成后执行：

~~~bash
node <skill>/scripts/check_page.cjs <报告目录>/index.html --shots /tmp/report-shots
~~~

然后实际看 desktop / mobile / dark 截图。自动体检抓不到“第一屏看不懂”“图被压扁”“重点被埋没”。

验证、自包含、来源、敏感信息、README、媒体和端口分享见 `references/delivery-and-validation.md`。

### 8. 交付一个目录

默认：

~~~text
reports/<主题>/
  index.html
  README.md
  data.json / *.csv   # 有结构化数据时
  assets/             # 有必须外置的媒体时
~~~

README 至少写：目的、来源范围/as-of、完整重跑命令或生成方法、主要输入版本、体积、与上一版差异、未完成验证。

只有用户需要链接时才使用 `scripts/serve_report.sh`，不要默认开放端口。

## 按需读取参考资料

| 情况 | 读取 |
|---|---|
| 页面结构、KPI、图表、信息层级 | `references/report-structure.md` |
| 项目阶段总结、复盘、Decision/Ask、风险和 actions | `references/project-briefing.md` |
| 归因、消融、失败、因果措辞、全条件证据 | `references/evidence-and-claims.md` |
| 分享前数字/口径/比较/偏差 QA | `references/analysis-validation.md` |
| 自包含、来源、敏感信息、README、浏览器 QA、端口分享 | `references/delivery-and-validation.md` |
| 复杂自定义图表 | 若环境里有专门数据可视化 skill，可额外参考；否则使用本 skill 原则和 `assets/charts.py` |

不要一次性读取所有 reference，只加载当前模式需要的部分。

## 完成标准

- 所有关键数字和项目事实都能追溯到结构化结果或明确来源。
- Hero 单独看就能回答“现在是什么状态、最重要发现是什么、为什么重要”。
- 未运行、未知/TBC、真实零分/无进展区分清楚。
- 项目汇报把 facts、risks、open questions、actions 分开；不虚构 owner/date/status。
- 结论措辞与证据强度匹配。
- 关键比较通过分享前 QA。
- 限制和来源范围在页面或 README 可见。
- 图表有等价数字表或可追溯导出。
- 报告能由生成器重建。
- `check_page.cjs` 已通过并查看截图，或明确记录未能执行的检查。
