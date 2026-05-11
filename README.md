# 🧠 Hermes Model Switcher

**Web 面板式 AI 模型一键切换工具** — 为 [Hermes Agent](https://github.com/nous-hermes/hermes-agent) 而生，支持在浏览器里点一下即可切换默认的 LLM provider / model。

> ✅ v0.2.0 — 通用版（动态发现 hermes，跨机器部署）

---

## ✨ 功能

- 🌐 **可视化管理** — 深色主题 Web UI，直观展示所有 provider 和 model
- ⚡ **一键切换** — 点模型名即时切换 Hermes 默认 provider/model
- 🔄 **自动刷新** — 切换后立刻更新当前选中状态
- ✅ **回读校验** — 切换后重新读取 `config.yaml`，确认真实生效
- 🩺 **健康检查接口** — 提供 `/api/health` 便于排障与自动化检测
- 📦 **开机自启** — systemd user 服务，重启机器后自动拉起
- 🔌 **API 驱动** — 前后端分离，REST API 供脚本/CI 调用
- 🌍 **跨机器可复用** — 自动发现 hermes CLI，避免写死路径

---

## 🚀 快速开始

### 前提条件

- 已安装 [Hermes Agent CLI](https://hermes-agent.nousresearch.com/docs)
- `~/.hermes/config.yaml` 已配置好 providers 和 models
- Python 3.8+ 和 `pyyaml`
- Linux / WSL（systemd user 可用）

### 1) 安装依赖

```bash
pip install pyyaml
```

### 2) 安装并启动

```bash
cd ~/.hermes/model-switcher
chmod +x install.sh ctl.sh
./install.sh
```

访问：**http://localhost:8899**

### 3) 其他启动方式

```bash
# 方式 A：前台运行（调试）
python3 server.py

# 方式 B：后台运行
./ctl.sh start
```

---

## 📡 API

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/` | 面板页面 |
| `GET` | `/api/models` | 获取所有 provider / model 列表及当前默认值 |
| `GET` | `/api/health` | 获取服务健康状态、hermes 路径、当前模型等 |
| `POST` | `/api/switch` | 切换默认模型（body: `{"provider":"...", "model":"..."}`） |

### 示例

```bash
# 查看当前模型
curl --noproxy '*' http://localhost:8899/api/models

# 查看健康状态
curl --noproxy '*' http://localhost:8899/api/health

# 切换到 DeepSeek V4 Pro
curl --noproxy '*' -X POST http://localhost:8899/api/switch \
  -H 'Content-Type: application/json' \
  -d '{"provider":"deepseek","model":"deepseek-v4-pro"}'
```

### 自定义 hermes 路径（可选）

如果 `hermes` 不在 PATH，可设置环境变量：

```bash
export HERMES_BIN=/your/path/to/hermes
python3 server.py
```

---

## 🖥️ 界面

深色主题 Web UI，Provider / Model 双栏布局，点击模型名即时切换，当前选中高亮。

---

## 🛠️ 运维命令

```bash
# systemd 管理
systemctl --user status  model-switcher.service
systemctl --user restart model-switcher.service
systemctl --user stop    model-switcher.service
journalctl --user -u model-switcher.service -f

# 手动管理
./ctl.sh start
./ctl.sh stop
./ctl.sh status

# 健康检查
curl --noproxy '*' http://localhost:8899/api/health

# 端口占用检查
fuser 8899/tcp
```

---

## 🏗️ 项目结构

```text
model-switcher/
├── server.py               # Python 后端（HTTP 服务 + API + hermes CLI 调用）
├── index.html              # 前端页面（深色主题单页应用）
├── ctl.sh                  # 启停脚本
├── model-switcher.service  # systemd user 单元模板
├── install.sh              # 一键安装脚本
├── .pid                    # 运行时 PID 文件（已 gitignore）
└── README.md
```

---

## 🔐 安全

- 监听 `0.0.0.0:8899`，仅推荐在内网/本机使用
- 如需外部访问请加反向代理 + 认证
- 不会直接操作 `config.yaml` 的 API key（只改 `model.default` / `model.provider`）
- 当前会话不会热切模型，**新会话**才会使用切换后的默认模型

---

## 📋 版本历史

| 版本 | 日期 | 内容 |
|------|------|------|
| `v0.2.0` | 2026-05-11 | 通用版：动态发现 hermes，支持跨机器部署；新增 health 接口与回读校验 |
| `v0.1.0` | 2026-05-11 | 首个可用版：Web 切换 + systemd 自启 + hermes CLI 切换 |

---

## ⚙️ 许可证

MIT
