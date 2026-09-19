# skills

给 [Claude Code](https://claude.com/claude-code) 用的 skill 集合。
每个子目录是一个独立的 skill，含 `SKILL.md` 和它需要的脚本与资产。

## 安装

拷到 Claude Code 的 skill 目录即可，不需要注册或构建：

```bash
git clone https://github.com/ioyy900205/skills.git
cp -r skills/experiment-briefing ~/.claude/skills/
```

放在 `~/.claude/skills/` 下对所有项目生效；只想给某个项目用就放到该项目的
`.claude/skills/` 下。装好后 Claude 会按 `SKILL.md` 里的描述自动判断何时调用，
也可以直接让它用某个 skill。

## 目录

### [`experiment-briefing`](experiment-briefing/)

把实验、评测、分析的结果做成一页汇报 HTML——**同时给领导和给自己看**。
领导三十秒要拿到结论，自己三个月后要能追溯每个数字怎么来的，靠分层解决。

固化的做法：

- **生成器是唯一真相源。** 页面里每个数字都从运行目录读回，不手敲。改页面 = 改脚本，
  永不手改生成出来的 HTML。手敲的数字会在下一次重跑后变成谎言。
- **结论先行的章节骨架。** 标题写结论不写主题；KPI 是对比不是孤立数字；
  每张图后面跟要点列表，其中至少一条是限定或反直觉的。
- **覆盖全条件，失败照实。** 不做只挑成功的画廊；"没跑成"和"得零分"用不同画法；
  区分"原理上做不到"和"能改进"——不写清楚，读者会把物理极限记成缺陷。
- **分清证据强度。** 恒等式拆分能说"占多少"，消融只能说"改掉它会怎样"，
  后者横着加不起来，不能并排写成一条因果链。
- **交付一个目录**：页面 + README（起因、重跑命令、体积、与上版差别）+ 数据导出（CSV/JSON）。

自带的工具：

| 文件 | 作用 |
|---|---|
| `assets/report_template.py` | 生成器骨架，拷走换掉 `MARKER` 就能跑 |
| `assets/report_html.py` | 设计系统、图片内嵌、表格、主题切换 |
| `assets/charts.py` | 内联 SVG 折线图与二维热图，亮暗两套已验证色阶 |
| `scripts/check_page.cjs` | 渲染体检：溢出、外链、tab 失效、暗色对比度、强制主题、JS 报错 |
| `scripts/serve_report.sh` | 开端口分享，只绑单网卡、只发布报告目录、只读 |

体检脚本需要 playwright：`npm i playwright && npx playwright install chromium`。

### [`update-agent-clis`](update-agent-clis/)

更新本机的 agent CLI 工具（Claude Code、Codex、Gemini CLI、dsh 等）——**镜像优先，先探测再动手**。
国内直连 `registry.npmjs.org` 实测约 40 KB/s，而带原生二进制的 agent CLI 动辄上百 MB，
选错源就是几十分钟的事。

固化的做法：

- **先探测，不急着装。** 先跑只读脚本得到一张表，标着 `已最新` 的工具绝不重装——
  重装 codex 意味着白下 135 MB，换来的收益是零，还平白引入一次命令失效窗口。
- **镜像按命令传参，不写全局配置。** `--registry=https://registry.npmmirror.com`
  只作用于当次安装，不动 `~/.npmrc`，其它 npm 工作流（公司私有源之类）不受影响。
  换源前先核对两边的 shasum 一致，确认是同一份文件。
- **装到一半绝不 kill。** npm 的 reify 阶段会先删掉旧版 bin 软链、再放新的，
  中断会让 CLI 命令直接消失。卡住时别猜，去看缓存临时文件的字节数是否在涨——
  在涨就是在下载，等着。
- **不用 `claude update` 更新 npm 装的 claude。** 它会把 `~/.local/bin/claude`
  这种软链误判成第二份独立的 native 安装，可能装出双份来打架。
- **装完必须验。** 只看 npm 的输出不够：跑 `--version`，再核对 bin 软链时间戳，
  确认没被同一次安装波及。

自带的工具：

| 文件 | 作用 |
|---|---|
| `scripts/check_agents.py` | 只读探测：当前版本、最新版本、安装方式、建议升级命令。从二进制的真实路径反推包名，比硬编码映射表可信 |

只依赖 python3 和标准库，不需要额外安装。

## 来历

这些 skill 是从真实项目里长出来的，不是凭空设计的——规矩基本对应踩过的坑。
例如"强制主题"那条体检，来自一次真实缺陷：暗色样式只写在
`@media (prefers-color-scheme: dark)` 里时，切换按钮只能强制亮、不能强制暗，
而后者恰好是亮色笔记本的读者会碰到的方向。

`update-agent-clis` 同理。它成文于一次更新 codex 的过程：官方源下到 65 MB 时
估算还要 40 分钟，换镜像后 20 秒装完——于是"镜像优先"成了第一原则。而"绝不中断
安装"那条是被吓出来的：下载那十几分钟里 `codex` 命令其实是消失状态，因为 npm
已经先删了旧软链。当时没中断是运气，"不要中断"是事后才想明白的道理。
