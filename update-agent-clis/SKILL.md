---
name: update-agent-clis
description: 更新本机的 agent CLI 工具（Claude Code、Codex、Gemini CLI、Qwen Code、dsh、aider 等）。用户想更新或升级这些 CLI、想知道它们是不是最新版、嫌版本太旧，或者问某次更新进展如何、为什么卡住时使用——包括没点名具体工具、只泛泛说"更新 agent / 升级 CLI"的情况。核心是镜像优先且镜像必须直连：本机环境变量设了 http(s)_proxy，npm 经代理访问 npmmirror 只有约 20 KB/s，加 --noproxy=npmmirror.com 直连可达 6~13 MB/s；一律按命令传参，不改全局配置。
---

# 更新 agent CLI

## 这个 skill 解决什么

带原生二进制的 agent CLI 动辄上百 MB：codex 0.158.0 的 linux-x64 平台包 tarball 有 **162 MB**（解压后 424 MB）。走哪条路下载，速度能差几百倍。2026-09-28 本机实测：

| 源 | 经代理（`$https_proxy`） | 直连 |
|---|---|---|
| npmmirror（registry + cdn） | **约 20 KB/s** | 6~13 MB/s |
| registry.npmjs.org（官方） | 1.8 MB/s | 2.2 MB/s |
| 清华 PyPI | 5.9 MB/s | 5.4 MB/s |

本机 shell 的环境变量里设了 `http_proxy` / `https_proxy`，npm、pip、curl 都会自动走它。所以这个 skill 的第一原则有两半：**镜像优先**，并且**镜像必须直连**。经代理访问 npmmirror 是所有路径里最慢的，比官方源还慢近 100 倍。这是实际踩过的：codex 更新经代理跑了 20 分钟只下了 27 MB，改直连后 12 秒下完。

第二件事是流程要稳：npm 安装过程中有一步会让 CLI 短暂不可用，这时候误操作会把工具弄坏（下面"雷区"一节详述）。

## 工作流

### 1. 先探测，别急着装

```bash
python3 <skill目录>/scripts/check_agents.py
```

脚本只读不写，输出一张表：每个 agent CLI 的当前版本、最新版本、安装方式、升级命令。已是最新的会标 `已最新`，升级命令显示 `-`。

**看到 `已最新` 就绝不要重装。** 重装 codex 意味着白下 162 MB，而且过程中 CLI 还会短暂失效。这是这个 skill 最实际的省事之处。

只想查某几个就传名字：`python3 scripts/check_agents.py claude codex`。

### 2. 把结果告诉用户

原样贴出表，让用户看到全貌——包括"已最新"的那些。如果全部已最新，直接说一句就结束，不要为了显得干了活而做多余动作。

### 3. 逐个更新

用表里 `升级命令` 列给出的命令，它已经带好了镜像和直连参数：

```bash
npm install -g @openai/codex@latest --registry=https://registry.npmmirror.com --noproxy=npmmirror.com
```

`--noproxy=npmmirror.com` 不能省，见雷区"镜像必须直连"。

**给足超时**：直连镜像正常十几秒到几十秒，网络抖动时可能到几分钟。`timeout` 至少给 600000 ms（10 分钟）。

**装到一半超时了怎么办**：命令会被挪到后台继续跑，这是好事。先按雷区"绝对不要在 npm 安装中途 kill"里的方法判断：是在正常下载，还是被代理拖住了。正常下载就**等它跑完，绝对不要 kill**，跑的过程中可以先做别的，完成后验证；被代理拖住的，按同一条里的救援步骤处理。

### 4. 验证

装完必须验，不要只看 npm 的输出：

```bash
claude --version && codex --version
```

如果版本没变，或命令报 `command not found` / `No such file or directory`，去看雷区"绝对不要在 npm 安装中途 kill"。

### 5. 报告

说清楚：谁从什么版本升到了什么版本、哪些本来就已经最新、过程中有什么值得注意的（比如换了源、卡了多久）。**失败的照实说**，不要只报成功的。

## 雷区

这些都是实际踩过的，不是理论风险。

### 1. 镜像必须直连，别让环境变量里的代理截走

本机 shell 设了 `http_proxy` / `https_proxy`（指向一台内网 HTTP 代理），`no_proxy` 只覆盖 localhost 和内网网段、内网域名，不含 npmmirror。npm 默认读这些变量，所以即使传了 `--registry=https://registry.npmmirror.com`，请求照样全部绕道代理。症状：

- 元数据请求慢得离谱：debug 日志（`~/.npm/_logs/*-debug-0.log`）里是 `http fetch GET 200 https://registry.npmmirror.com/@openai%2fcodex 78595ms`，直连只要 0.4 秒
- 平台包按约 20 KB/s 下载，162 MB 要两个多小时
- `check_agents.py` 旧版的 `npm view` 撞上 40 秒超时，表里显示"未知"

**做法**：npm 命令加 `--noproxy=npmmirror.com`。npm 的 noproxy 按域名后缀逐段匹配，`npmmirror.com` 同时覆盖 `registry.npmmirror.com` 和 tarball 实际所在的 `cdn.npmmirror.com`（registry 会 302 过去）。已用假代理做过确定性验证：把 `https_proxy` 指向不存在的 `127.0.0.1:9`、用空缓存目录，加这个参数能正常 `npm view`，不加就报 `ECONNREFUSED`。

**是 `--noproxy`，不是 `--no-proxy`。** 后者只是把 `proxy` 配置设成 false，而 npm（`@npmcli/agent` 的 `getProxy`）遇到假值会回落去读环境变量，照样走代理，同样的假代理测试下报 `ECONNREFUSED`。

**诊断一个正在跑的 npm 有没有走代理**：

```bash
ss -tnp | grep "pid=<npm 的 pid>"
```

对端是 `$https_proxy` 里的那个地址（`echo $https_proxy` 可查），就是走了代理。

代理只拖慢 npmmirror：同一个代理访问官方 npmjs（1.8 MB/s）和清华 PyPI（5.9 MB/s）都不慢，所以 pip 命令不用改。真遇到 pip 慢，也可以用 `no_proxy=pypi.tuna.tsinghua.edu.cn pip install ...` 让 pip 直连（同样用假代理验证过）。反过来，如果某台机器直连镜像不通（`curl --noproxy '*' -sI https://registry.npmmirror.com` 超时，比如不能出网的集群节点），就去掉 `--noproxy`，退回走代理。

和"不改全局配置"那条同理：只按命令传参，不要去改 `~/.bashrc` 里的 `no_proxy`，也不要写 `~/.npmrc`。

### 2. 绝对不要在 npm 安装中途 kill

npm 的 reify 阶段在**下载之前**就把旧版挪进隐藏目录：`lib/node_modules/@openai/.codex-<8位hash>` 和 `bin/.codex-<hash>`。所以在下载那段时间里，CLI 命令其实是消失状态：`codex --version` 会报 `command not found` 或 `No such file or directory`。此时如果以为"卡死了"而 kill，工具就一直坏着，直到下次装完才恢复。

还有个反直觉的地方：**第一次 Ctrl-C / SIGTERM 停不下来**。arborist 会接住第一个信号（SIGINT、SIGTERM、SIGHUP 等都在列），只记个标记，要等当前步骤（也就是那段下载）结束后才回滚。第二个信号才让进程立即退出，而这时不会回滚，旧版就留在隐藏目录里。

**判断是否该等**：

1. `ps` 确认 `npm install` 进程还活着
2. `ls -la ~/.npm/_cacache/tmp/`，隔 20 秒再看一次，用大文件字节数的增长算出下载速度
3. `ss -tnp | grep "pid=<pid>"` 看有没有走代理（见上一条）

字节数在涨、按这个速度几分钟内能下完，就等着。

**被代理拖住（要几个小时）时的救援**，2026-09-28 实操过，全程约 1 分钟：

```bash
# 1. 先直连把大包预取进缓存：不碰正在跑的进程，顺带验证直连可用
npm cache add @openai/codex@<版本>-linux-x64 --registry=https://registry.npmmirror.com --noproxy=npmmirror.com
# 2. 中断旧进程，要发两次（第一次会被接住）
kill -TERM <pid>; sleep 3; kill -TERM <pid>
# 3. 立刻直连重装：tarball 命中缓存，几秒完成
npm install -g @openai/codex@latest --registry=https://registry.npmmirror.com --noproxy=npmmirror.com
```

第 1 步的包规格从 debug 日志里正在下载的 tarball 地址推出来：`.../@openai/codex/-/codex-0.158.0-linux-x64.tgz` 对应 `@openai/codex@0.158.0-linux-x64`。codex 的平台包是以 `@openai/codex` 特殊版本号的形式发布的，日志里的 `@openai/codex-linux-x64` 只是别名，不能直接拿去 `cache add`。

隐藏目录不用手动清：目录名取自路径的 sha1，是固定的，重装时 npm 会覆盖同名遗留，装完一并删掉。**想回退旧版**的话，要在重装**之前**把 `.codex-<hash>` 挪回原名。被 kill 的进程还会在 `~/.npm/_cacache/tmp/` 留下半截文件，确认没有 npm 在跑后可以删。

### 3. 别用 `claude update` 更新 npm 装的 claude

`claude update` 会自己探测安装方式，但它对**软链**判断有误。本机 `~/.local/bin/claude` 只是指向 nvm 里那份 npm 安装的软链，`claude update` 却报告：

```
Warning: Multiple installations found
- npm-global at .../nvm/versions/node/v24.16.0/bin/claude (currently running)
- native at /home/<user>/.local/bin/claude
```

它把软链当成了第二份独立的 native 安装。真让它执行更新，可能装出第二份、造成版本打架。**npm 装的就用 npm 更新**，路径统一、可预测。

### 4. 换源之前先核对哈希

打算从一个源切到另一个源时，先确认两边是同一份文件：

```bash
curl -s 'https://registry.npmjs.org/<pkg>/<version>' | python3 -c "import sys,json; print(json.load(sys.stdin)['dist']['shasum'])"
curl -s --noproxy npmmirror.com 'https://registry.npmmirror.com/<pkg>/<version>' | python3 -c "import sys,json; print(json.load(sys.stdin)['dist']['shasum'])"
```

两个 shasum 一致才切。npmmirror 是官方 tarball 的忠实镜像（本机核对过 `@openai/codex@0.155.1-linux-x64` 两边同为 `b4fcbdb002086a186a5a3e76b0e49326a02e1582`，`@openai/codex@0.158.0-linux-x64` 两边同为 `acb0b1f56d5580d6c9266fe1c00caed32dedacb9`），npm 安装时还会再校验 integrity，所以核对通过后是安全的。

### 5. 不改全局 registry 配置

用 `--registry=` / `--noproxy=` 按命令传参，**不要**写 `~/.npmrc`。理由：用户的其它 npm 工作流（公司私有 registry、需要官方源的场景）不该被这个 skill 改变行为；按命令传参随时可回退，零副作用。

### 6. nvm 切换 node 版本会让 CLI 消失

本机的 claude / codex 装在 `~/.nvm/versions/node/v24.16.0/lib/node_modules/` 下。如果用户 `nvm use` 到别的 node 版本，这两个命令会从 PATH 上消失——**这不是安装失败**。遇到"命令找不到"时先确认 `node -v` 是不是还是装机时那个版本。

## 扩展

`scripts/check_agents.py` 顶部的 `KNOWN` 列表是候选清单，元素是 `(二进制名, 来源, 包名)`，来源支持 `npm` / `pypi` / `other`。装了新 CLI 就往里加一行。

脚本会**从二进制的真实路径反推包名**（解析软链后取 `node_modules/` 后面那段），这比硬编码的映射表可信，因为路径反映实际安装位置——所以注册表里的包名填错了也能被路径纠正。表头对齐靠 `display_width()` 按东亚全角字符算 2 列，中文才不会错位。

脚本查 npm 最新版时同样直连镜像（`npm view` 带 `--noproxy`）。pypi 的最新版用 `pip index versions` 问镜像，**不用镜像的 JSON API**：清华的 `/pypi/<包>/json` 数据陈旧（2026-09-28 aider-chat 在那里还是 0.50.1，官方已是 0.86.2），simple 索引才是新的，而 pip 读的正是 simple 索引。simple 索引 JSON 里的 `versions` 字段是按字符串排的（`0.9.0` 排在 `0.86.2` 后面），不能直接取最后一个。镜像地址可用环境变量 `NPM_MIRROR` / `NPM_NOPROXY` / `PIP_MIRROR` 覆盖。

不在列表里的 CLI 也能查：先 `command -v <名字>` 找到路径，`readlink -f` 解析软链，看是不是落在某个 `node_modules/` 下——是的话就按 npm 全局包处理，不是的话多半是自更新或 curl 装的原生二进制（goose、cursor-agent 属于这类），让用户用该工具自带的自更新命令。

## 相关

pip 装的 agent（如 aider）同理走镜像：`pip install -U aider-chat -i https://pypi.tuna.tsinghua.edu.cn/simple`。清华 pypi 镜像是国内同类问题的对应解法，它经代理也不慢（见雷区"镜像必须直连"），不用加 `no_proxy`。
