# AutoGLM Browser Agent — 安装指南

本文档说明首次安装所需的全部步骤。安装完成后日常使用请参阅 `SKILL.md`。

---

## 1. 选择浏览器（必选）

**⚠️ 必须先确认用户使用哪个浏览器，后续所有步骤都依赖此选择。**

**向用户询问**：

> 你使用哪个浏览器？
> - **Chrome**
> - **Edge**

用户选择后，写入配置文件：

```bash
# macOS / Linux
mkdir -p ~/.openclaw-autoclaw

# 用户选择 Chrome
echo '{"browser": "chrome"}' > ~/.openclaw-autoclaw/config.json

# 用户选择 Edge
echo '{"browser": "edge"}' > ~/.openclaw-autoclaw/config.json
```

```bat
:: Windows
if not exist "%USERPROFILE%\.openclaw-autoclaw" mkdir "%USERPROFILE%\.openclaw-autoclaw"

:: 用户选择 Chrome
echo {"browser": "chrome"} > "%USERPROFILE%\.openclaw-autoclaw\config.json"

:: 用户选择 Edge
echo {"browser": "edge"} > "%USERPROFILE%\.openclaw-autoclaw\config.json"
```

> 后续可随时说"用 Edge"/"用 Chrome"来切换。

---

## 2. macOS 解除安全限制（仅 macOS 需要）

首次下载后，macOS 会阻止未签名的二进制文件运行。执行以下命令解除：

```bash
xattr -d com.apple.quarantine {baseDir}/dist/relay {baseDir}/dist/mcp_server {baseDir}/dependency/mcporter
```

> Windows 用户跳过此步骤。

---

## 3. 安装浏览器扩展

根据步骤 1 选择的浏览器，安装对应扩展：

**Chrome / Brave / Arc**：

打开链接安装：[AutoGLM 扩展（Chrome Web Store）](https://chromewebstore.google.com/detail/autoglm/jelniggicmclhfgnlapbkgfibmgelfnp?hl=zh-CN&utm_source=ext_sidebar)

**Edge**：

打开链接安装：[AutoGLM 扩展（Edge Add-ons）](https://microsoftedge.microsoft.com/addons/detail/autoglm/ljlnbmmmgnflklegiafalpieckpihffn)

**安装后验证**：

1. 打开 `chrome://extensions/`（Chrome）或 `edge://extensions/`（Edge）
2. 确认 AutoGLM 扩展已出现且开关为**开启状态**
3. 如果扩展被禁用，点击开关启用

---

## 4. 注册 MCP Server

mcporter 已内置在 `{baseDir}/dependency/` 目录中，无需单独安装。

**macOS / Linux**：

```bash
{baseDir}/dependency/mcporter config add autoglm-browser-agent --stdio "{baseDir}/dist/mcp_server --start_url https://www.bing.com --window_width 1456 --window_height 819 --resize_width 1456 --resize_height 819 --max_steps 100 --log_dir {baseDir}/mcp_output --if_subagent"
```

**Windows**（推荐使用 cmd）：

```bat
{baseDir}\dependency\mcporter.exe config add autoglm-browser-agent --command "{baseDir}\dist\mcp_server.exe" --arg --start_url --arg https://www.bing.com --arg --window_width --arg 1456 --arg --window_height --arg 819 --arg --resize_width --arg 1456 --arg --resize_height --arg 819 --arg --max_steps --arg 100 --arg --log_dir --arg "{baseDir}\mcp_output" --arg --if_subagent
```

验证注册成功：

```bash
# macOS / Linux
{baseDir}/dependency/mcporter list autoglm-browser-agent --schema

# Windows
{baseDir}\dependency\mcporter.exe list autoglm-browser-agent --schema
```

---

## 5. 启动 WS Relay Daemon

Relay 保持浏览器扩展的 WebSocket 长连接，防止 mcporter call 结束后浏览器窗口关闭。

```bash
# macOS / Linux
{baseDir}/dist/relay

# Windows
{baseDir}\dist\relay.exe
```

日志输出到 `{baseDir}/mcp_output/relay.log`。

---

## 6. 配置信任模式（auto_approve）

信任模式控制敏感操作（发评论、点赞、发帖、发消息等）是否自动执行：
- **关闭（默认）**：每次敏感操作暂停询问用户确认后才执行
- **开启**：敏感操作自动执行，不再逐次确认
- **无论开关，登录和验证码始终需要用户手动操作**

**询问用户是否开启信任模式**，根据回答写入配置（与步骤 1 的浏览器选择合并到同一个 config.json）：

```bash
# macOS / Linux — 读取现有 config.json 并合并 auto_approve 字段
# 用户同意开启信任模式：将 auto_approve: true 合并写入
# 用户拒绝：将 auto_approve: false 合并写入
```

> **注意**：步骤 1 已写入 browser 字段，这里需要**合并**写入（读取现有 config.json，加上 auto_approve 字段后写回），不要覆盖已有配置。

> 后续使用中用户可随时说"开启/关闭信任模式"来切换。
