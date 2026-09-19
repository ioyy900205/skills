# 交付、验证与分享

## 自包含优先

默认生成单文件 HTML：

- CSS/JS 内联。
- 普通图片可用 `report_html.py` 的 embed() 转 WebP 后 base64 内嵌。
- 不依赖 CDN、在线字体或外部脚本。

这样报告可以直接发文件、离线打开，也不依赖服务器继续运行。

## 音频和视频例外

如果证据需要试听/播放，而且媒体很多，不要全部 base64 内嵌。

推荐结构：

~~~text
report/
  index.html
  assets/
    sample_001.wav
    sample_002.wav
~~~

HTML 使用相对路径，并设置 `preload="none"`，避免页面打开时同时读取大量媒体。

README 写明总大小和媒体占用。

## 来源与更新时间

项目总结、复盘、decision brief 等多来源报告，在页面底部列出真正使用过的主要来源。

来源应具体到可复核，例如：运行目录、summary 文件、代码路径、commit/PR/issue、会议材料、用户提供文件或 URL。

持续更新的报告显示 **As of / Last updated**。如果某个来源本次不可访问，把这个 gap 写出来；“没搜到”不等于“没发生”。

## 分享前敏感信息检查

HTML 是可转发的，默认按“会离开当前机器”处理。

嵌入以下内容前检查并脱敏：

- API key / token / password / private key。
- Authorization/Cookie header。
- 含凭据的连接字符串。
- 带 token/signature 的 URL。
- 日志、git diff、配置和会议消息里偶然出现的凭据。

用 `<REDACTED:TYPE>` 之类占位符保留语义。发现真实仍有效的凭据时，不只在报告中脱敏，还要告诉用户源位置存在泄漏风险。

## 浏览器体检

运行：

~~~bash
node <skill>/scripts/check_page.cjs <报告目录>/index.html --shots /tmp/report-shots
~~~

它主要检查：

- 重复 id。
- 桌面和 390px 窄屏横向溢出。
- 外链 CSS/JS/图片。
- 图片加载失败。
- sticky header 遮挡锚点。
- tab 是否真的能切换出内容。
- 手动强制亮/暗主题是否工作。
- 暗色模式关键文字对比度。
- JS/console 错误。

需要 Playwright。若不可用，明确说明浏览器级 QA 未完整执行。

## 必须看截图

自动检查通过后，至少看 desktop、mobile、dark。

重点判断自动脚本判断不了的问题：第一屏能否直接读懂、图是否被压扁、标题是否太长、图例是否难懂、重要 caveat 是否被埋没。

## README

README 与页面服务不同读者。

页面回答“结论/状态是什么”。

README 至少回答：

- 为什么做这次实验/项目总结。
- 来源范围与 as-of。
- 完整重跑/重新生成命令。
- 关键输入、配置、数据和权重版本/哈希。
- 输出目录结构。
- 页面和媒体体积。
- 与上一版的差别。
- 已知限制、缺失来源或没有执行的验证步骤。

## 数据导出

存在结构化数据时，页面旁边放 CSV 或 JSON。

它不一定被网页读取，但要让别人能复核、切片或继续分析，而不是只能从截图抄数。

## 端口分享

只有用户明确需要链接时，再运行：

~~~bash
<skill>/scripts/serve_report.sh start <报告目录> --port 8845
~~~

保留：

- 只绑定明确网卡，不默认 0.0.0.0。
- 只发布报告目录，不发布仓库根。
- 使用只读静态服务。
- 不加入上传/写入能力。

分享结束后可用 status / stop / list 管理实例。
