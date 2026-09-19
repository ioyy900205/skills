#!/usr/bin/env python3
"""扫描本机已安装的 agent CLI，输出：当前版本、最新版本、安装方式、建议升级命令。

只读取信息，不做任何修改——升级由调用方看完结果后再决定。

用法：
    check_agents.py            # 全部候选
    check_agents.py codex      # 只查指定的几个
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
import urllib.request

# 镜像：国内直连 registry.npmjs.org 实测约 40 KB/s，npmmirror 约 200 KB/s。
# codex 的平台包 tarball 有 135 MB，走官方源要 40 分钟，走镜像 20 秒。
NPM_MIRROR = os.environ.get("NPM_MIRROR", "https://registry.npmmirror.com")
PIP_MIRROR = os.environ.get("PIP_MIRROR", "https://pypi.tuna.tsinghua.edu.cn/simple")

# 候选注册表：(二进制名, 来源, 包名)
# 来源为 npm / pypi 时包名必填；other 表示非包管理器安装（自更新或 curl 装的原生二进制）。
# 这张表只是"起点"，不是白名单——PATH 上还有别的 agent CLI 时，
# 用下面的 derive_npm_pkg 单独查它即可。
KNOWN: list[tuple[str, str, str]] = [
    ("claude", "npm", "@anthropic-ai/claude-code"),
    ("codex", "npm", "@openai/codex"),
    ("gemini", "npm", "@google/gemini-cli"),
    ("qwen", "npm", "@qwen-code/qwen-code"),
    ("opencode", "npm", "opencode-ai"),
    ("crush", "npm", "@charmland/crush"),
    ("amp", "npm", "@sourcegraph/amp"),
    ("dsh", "npm", "@deepseek-ai/dsh"),
    ("aider", "pypi", "aider-chat"),
    ("goose", "other", ""),
    ("cursor-agent", "other", ""),
]

VERSION_RE = re.compile(r"\d+\.\d+\.\d+(?:[.-][0-9A-Za-z.]+)?")


def run(cmd: list[str], timeout: int) -> str:
    """跑一条命令取 stdout；失败或超时返回空串，绝不抛异常打断整张表。"""
    try:
        out = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
        return out.stdout
    except (subprocess.TimeoutExpired, OSError):
        return ""


def current_version(binary: str) -> str:
    """跑 <binary> --version 并抠出版本号。

    多数 CLI 的输出里混着工具名（如 'codex-cli 0.155.1'），所以用正则抠而不是直接取整行。
    """
    out = run([binary, "--version"], timeout=20) or run([binary, "-V"], timeout=20)
    m = VERSION_RE.search(out)
    return m.group(0) if m else "?"


def latest_version(source: str, pkg: str) -> str:
    if source == "npm":
        out = run(["npm", "view", pkg, "version", "--registry", NPM_MIRROR], timeout=40)
        m = VERSION_RE.search(out)
        return m.group(0) if m else ""
    if source == "pypi":
        url = f"{PIP_MIRROR.rstrip('/')}/{pkg}/json"
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                return json.load(resp)["info"]["version"]
        except Exception:
            return ""
    return ""


def derive_npm_pkg(real_path: str) -> str | None:
    """从二进制真实路径反推 npm 包名。

    比硬编码的映射表可信，因为路径反映的是实际安装位置。
    例：.../lib/node_modules/@openai/codex/bin/codex.js -> @openai/codex
    """
    marker = "/node_modules/"
    if marker not in real_path:
        return None
    rest = real_path.split(marker, 1)[1]
    parts = rest.split("/")
    if rest.startswith("@") and len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    return parts[0] if parts and parts[0] else None


def display_width(s: str) -> int:
    """终端显示宽度：东亚全角字符占 2 列。表格对齐全靠它。"""
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


def pad(s: str, width: int) -> str:
    return s + " " * max(0, width - display_width(s))


def render_table(rows: list[list[str]]) -> str:
    cols = len(rows[0])
    widths = [max(display_width(r[i]) for r in rows) for i in range(cols)]
    lines = []
    for idx, row in enumerate(rows):
        lines.append("  ".join(pad(c, widths[i]) for i, c in enumerate(row)).rstrip())
        if idx == 0:  # 表头下加分隔线
            lines.append("  ".join("-" * w for w in widths))
    return "\n".join(lines)


def main() -> int:
    wanted = set(sys.argv[1:])

    rows: list[list[str]] = [["名称", "当前", "最新", "状态", "安装方式", "升级命令"]]

    for name, source, pkg in KNOWN:
        if wanted and name not in wanted:
            continue

        binpath = shutil.which(name)
        if not binpath:
            continue  # 没装就跳过，不刷屏

        # 解析软链后的真实路径——本机 .local/bin/claude 就是指向 nvm 里 npm 安装的软链，
        # 不解析的话会把同一份安装误判成两份（claude update 就栽在这上面）。
        real = os.path.realpath(binpath)

        # 路径能反推出包名时以路径为准（它是事实），否则退回注册表里的值
        derived = derive_npm_pkg(real)
        if derived:
            source, pkg = "npm", derived

        cur = current_version(name)
        lat = latest_version(source, pkg)

        if source == "npm":
            how = f"npm-global({pkg})"
            cmd = f"npm install -g {pkg}@latest --registry={NPM_MIRROR}"
        elif source == "pypi":
            how = f"pypi({pkg})"
            cmd = f"pip install -U {pkg} -i {PIP_MIRROR}"
        else:
            how = "手动安装"
            cmd = "用该工具自带的自更新命令，或查官方文档"

        if not lat:
            status, cmd = "未知", "（查不到最新版，见 SKILL.md 排查）"
        elif cur == lat:
            status, cmd = "已最新", "-"
        else:
            status = "可更新"

        rows.append([name, cur, lat or "?", status, how, cmd])

    if len(rows) == 1:
        print("没有探测到任何已安装的 agent CLI。")
        return 0

    print(render_table(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
