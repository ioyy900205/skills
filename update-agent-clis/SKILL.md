---
name: update-agent-clis
description: 更新本机的 agent CLI 工具（Claude Code、Codex、Gemini CLI、Qwen Code、dsh、aider 等）。当用户说"更新 claude"、"更新 codex"、"更新 agent"、"升级 agent 工具"、"升级 CLI"、"把命令行工具升到最新"、"check for updates"、"版本太旧了"、"升级一下 agent" 时使用。核心是镜像优先：本机直连 registry.npmjs.org 只有约 40 KB/s，走 npmmirror 快 5 倍，且必须按命令传参而非改全局配置。
---

# 更新 agent CLI

## 这个 skill 解决什么

本机（以及多数国内开发机）直连官方 npm 源极慢，实测约 **40 KB/s**；而带原生二进制的 agent CLI 动辄上百 MB。codex 的 linux-x64 平台包 tarball 有 **135 MB**（解压后 370 MB），走官方源要 40 分钟，走 npmmirror 20 秒。所以这个 skill 的第一原则是**镜像优先**。

第二件事是流程要稳：npm 安装过程中有一步会让 CLI 短暂不可用，这时候误操作会把工具弄坏（下面"雷区"一节详述）。

## 工作流

### 1. 先探测，别急着装

```bash
python3 <skill目录>/scripts/check_agents.py
```

脚本只读不写，输出一张表：每个 agent CLI 的当前版本、最新版本、安装方式、升级命令。已是最新的会标 `已最新`，升级命令显示 `-`。

**看到 `已最新` 就绝不要重装。** 重装 codex 意味着白下 135 MB，而且过程中 CLI 还会短暂失效。这是这个 skill 最实际的省事之处。

只想查某几个就传名字：`python3 scripts/check_agents.py claude codex`。

### 2. 把结果告诉用户

原样贴出表，让用户看到全貌——包括"已最新"的那些。如果全部已最新，直接说一句就结束，不要为了显得干了活而做多余动作。

### 3. 逐个更新

用表里 `升级命令` 列给出的命令，它已经带好了镜像参数：

```bash
npm install -g @openai/codex@latest --registry=https://registry.npmmirror.com
```

**给足超时**：镜像正常情况下几十秒，但网络抖动时可能到几分钟。`timeout` 至少给 600000 ms（10 分钟）。

**装到一半超时了怎么办**：命令会被挪到后台继续跑，这是好事。**等它跑完，绝对不要 kill**——原因见下方雷区。跑的过程中可以先做别的，完成后验证。

### 4. 验证

装完必须验，不要只看 npm 的输出：

```bash
claude --version && codex --version
```

如果版本没变或命令报 `No such file or directory`，去看雷区第 1 条。

### 5. 报告

说清楚：谁从什么版本升到了什么版本、哪些本来就已经最新、过程中有什么值得注意的（比如换了源、卡了多久）。**失败的照实说**，不要只报成功的。

## 雷区

这些都是实际踩过的，不是理论风险。

### 1. 绝对不要在 npm 安装中途 kill

npm 的 reify 阶段会**先删掉旧版的 bin 软链**，再放新的。所以在下载那段时间里，CLI 命令其实是消失状态：`codex --version` 会报 `No such file or directory`。此时如果以为"卡死了"而 Ctrl-C 或 kill，工具就一直坏着，直到下次装完才恢复。

**判断是否该等**：看 `ps` 确认进程还活着（`npm install` 进程在，且 CPU 时间在涨），再 `ls -la` npm 缓存临时目录（`~/.npm/_cacache/tmp/`）看那个大文件字节数是否在增长。在涨就是在下载，等着。

**唯一可以安全中断的时机**是下载阶段——但既然安全的中断时机和平安等待相差只有几分钟，而误判的代价是工具损坏，宁可等。

### 2. 别用 `claude update` 更新 npm 装的 claude

`claude update` 会自己探测安装方式，但它对**软链**判断有误。本机 `~/.local/bin/claude` 只是指向 nvm 里那份 npm 安装的软链，`claude update` 却报告：

```
Warning: Multiple installations found
- npm-global at .../nvm/versions/node/v24.16.0/bin/claude (currently running)
- native at /home/liuliang/.local/bin/claude
```

它把软链当成了第二份独立的 native 安装。真让它执行更新，可能装出第二份、造成版本打架。**npm 装的就用 npm 更新**，路径统一、可预测。

### 3. 换源之前先核对哈希

打算从一个源切到另一个源时，先确认两边是同一份文件：

```bash
curl -s 'https://registry.npmjs.org/<pkg>/<version>' | python3 -c "import sys,json; print(json.load(sys.stdin)['dist']['shasum'])"
curl -s 'https://registry.npmmirror.com/<pkg>/<version>' | python3 -c "import sys,json; print(json.load(sys.stdin)['dist']['shasum'])"
```

两个 shasum 一致才切。npmmirror 是官方 tarball 的忠实镜像（本机核对过 `@openai/codex@0.155.1-linux-x64` 两边同为 `b4fcbdb002086a186a5a3e76b0e49326a02e1582`），npm 安装时还会再校验 integrity，所以核对通过后是安全的。

### 4. 不改全局 registry 配置

用 `--registry=` 按命令传参，**不要**写 `~/.npmrc`。理由：用户的其它 npm 工作流（公司私有 registry、需要官方源的场景）不该被这个 skill 改变行为；按命令传参随时可回退，零副作用。

### 5. nvm 切换 node 版本会让 CLI 消失

本机的 claude / codex 装在 `~/.nvm/versions/node/v24.16.0/lib/node_modules/` 下。如果用户 `nvm use` 到别的 node 版本，这两个命令会从 PATH 上消失——**这不是安装失败**。遇到"命令找不到"时先确认 `node -v` 是不是还是装机时那个版本。

## 扩展

`scripts/check_agents.py` 顶部的 `KNOWN` 列表是候选清单，元素是 `(二进制名, 来源, 包名)`，来源支持 `npm` / `pypi` / `other`。装了新 CLI 就往里加一行。

脚本会**从二进制的真实路径反推包名**（解析软链后取 `node_modules/` 后面那段），这比硬编码的映射表可信，因为路径反映实际安装位置——所以注册表里的包名填错了也能被路径纠正。表头对齐靠 `display_width()` 按东亚全角字符算 2 列，中文才不会错位。

不在列表里的 CLI 也能查：先 `command -v <名字>` 找到路径，`readlink -f` 解析软链，看是不是落在某个 `node_modules/` 下——是的话就按 npm 全局包处理，不是的话多半是自更新或 curl 装的原生二进制（goose、cursor-agent 属于这类），让用户用该工具自带的自更新命令。

## 相关

pip 装的 agent（如 aider）同理走镜像：`pip install -U aider-chat -i https://pypi.tuna.tsinghua.edu.cn/simple`。清华 pypi 镜像是国内同类问题的对应解法。
