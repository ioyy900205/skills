# Skills

可复用的 AI Agent Skill 集合。每个 Skill 独立存放在自己的目录中，入口为 `SKILL.md`，详细原则、脚本和模板由该目录维护。

## Skills

| Skill | 用途 |
| --- | --- |
| [business-xray](business-xray/) | 企业价值穿透分析：纵、横、深、估，从财报事实到护城河、现金流与长期投资价值。 |
| [experiment-briefing](experiment-briefing/) | 将实验结果、项目进展和阶段复盘整理成可追溯的一页汇报。 |
| [project-orchestrator](project-orchestrator/) | 编排长期研发项目，协调 Agent、远程执行、GitHub、Linear 与 Notion。 |
| [update-agent-clis](update-agent-clis/) | 检查并更新 Claude Code、Codex 等 Agent CLI，优先使用可靠镜像。 |

## 安装

以 Claude Code 为例：

```bash
git clone https://github.com/ioyy900205/skills.git
cp -r skills/business-xray ~/.claude/skills/
```

需要其他 Skill 时，将 `business-xray` 换成对应目录名即可。仅在某个项目中使用时，可安装到该项目的 `.claude/skills/` 目录。

## 使用

直接描述任务，或明确指定 Skill，例如：

> 使用 business-xray 分析腾讯的长期盈利能力、护城河与当前估值。

具体用法与约束请阅读各目录的 `SKILL.md`；研究依据、资产和执行细节保留在 Skill 内，不在首页重复。
