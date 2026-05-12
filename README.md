# 🧠 Hermes Model Switcher

**Web 面板式 AI 模型一键切换工具** — 为 [Hermes Agent](https://github.com/nous-hermes/hermes-agent) 而生，支持在浏览器里一键切换 LLM provider/model，并管理多个 Hermes Agent（多 profile）。

> ✅ v0.4.0 — 生产加固：多线程服务 + CSS 分离 + 自动化测试

---

## ✨ 功能

- 🌐 **可视化管理** — 深色主题 Web UI，直观展示所有 provider 和 model
- 👥 **多 Agent (Profile)** — 顶部下拉切换 Hermes profile（default / finance / …），独立管理各自模型
- ⚡ **一键切换** — 点模型名即时切换对应 profile 的默认 provider/model
- 🔄 **自动刷新** — 切换后立刻更新当前选中状态
- ✅ **回读校验** — 切换后重新读取 `config.yaml`，确认真实生效
- 🩺 **健康检查** — 页面内置健康栏（服务状态 / hermes 可达性 / 最后更新时间）
- 🔁 **前端韧性** — 超时控制 + 自动重试，单次网络失败不崩溃
- 🧵 **并发安全** — `ThreadingHTTPServer`，切换模型时其他请求不阻塞
- 📦 **开机自启** — systemd user 服务，重启机器自动拉起
- 🔌 **API 驱动** — REST API 供脚本/CI 调用，profile 维度全覆盖
- 🌍 **跨机器可复用** — 自动发现 hermes CLI 和 python3 路径，避免写死
- ✅ **自动化测试** — 16 个单元测试覆盖核心逻辑

---

## 🚀 快速开始

### 前提

- [Hermes Agent CLI](https://hermes-agent.nousresearch.com/docs) 已安装
- `~/.hermes/config.yaml` 已配置好 provider 和 model
- Python 3.8+ 和 `pyyaml`
- Linux / WSL（systemd user 可用）

### 1) 安装依赖

```bash
pip install -r requirements.txt
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
# 前台（调试）
python3 server.py

# 后台
./ctl.sh start
```

---

## 🧪 测试

```bash
pip install pytest
pytest tests/ -v
```

---

## 👥 多 Profile（多 Agent）

如果你的 Hermes 有多个 profile（如 `default` + `finance`），页面顶部下拉可自由切换：

```
┌──────────────────┐
│ 🟢 default       │  ← 主 Agent
│ 💰 finance       │  ← 金融 Agent
└──────────────────┘
```

选哪个 profile，模型列表、健康栏、切换操作全自动联动。  
后端通过 `hermes --profile <name> config set ...` 写对应用户的 `config.yaml`。

Profile 目录约定：
```
~/.hermes/
├── config.yaml              ← default profile
└── profiles/
    └── finance/
        └── config.yaml      ← finance profile
```

---

## 📡 API

### 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/` | Web 面板页面 |
| `GET` | `/style.css` | 样式表（静态文件，1h 缓存） |
| `GET` | `/api/profiles` | 列出所有 profile 及当前模型摘要 |
| `GET` | `/api/models` | 获取 provider/model 列表（支持 `?profile=`） |
| `GET` | `/api/health` | 健康状态、hermes 可达性（支持 `?profile=`） |
| `POST` | `/api/switch` | 切换默认模型（body 支持 `profile` 字段） |

### 示例

```bash
# 查看所有 profile
curl --noproxy '*' http://localhost:8899/api/profiles

# 查看 default profile 的模型
curl --noproxy '*' http://localhost:8899/api/models

# 查看 finance profile 的模型
curl --noproxy '*' 'http://localhost:8899/api/models?profile=finance'

# 查看健康状态
curl --noproxy '*' http://localhost:8899/api/health
curl --noproxy '*' 'http://localhost:8899/api/health?profile=finance'

# 切换 default 模型的 provider/model
curl --noproxy '*' -X POST http://localhost:8899/api/switch \
  -H 'Content-Type: application/json' \
  -d '{"provider":"deepseek","model":"deepseek-v4-pro"}'

# 切换 finance profile 的模型
curl --noproxy '*' -X POST http://localhost:8899/api/switch \
  -H 'Content-Type: application/json' \
  -d '{"profile":"finance","provider":"custom:aicodemirror-claude","model":"claude-sonnet-4"}'
```

### 切换语义

- `profile` 未传或传 `"default"` → 操作 `~/.hermes/config.yaml`
- 传其他 profile 名（如 `"finance"`）→ 操作 `~/.hermes/profiles/finance/config.yaml`
- 切换通过 `hermes --profile <name> config set` 执行，并回读校验是否生效

---

## 🖥️ 界面

- 深色主题 Web UI
- Provider / Model 双栏布局，点击模型名即时切换
- 当前选中高亮，profile 顶部标识
- 健康栏：服务状态 / hermes 路径 / 最后更新时间
- 自动重试 + 超时兜底

---

## 🛠️ 运维命令

```bash
# systemd 管理
systemctl --user status  model-switcher.service
systemctl --user restart model-switcher.service
systemctl --user stop    model-switcher.service
journalctl --user -u model-switcher.service -f

# 手动启停
./ctl.sh start
./ctl.sh stop
./ctl.sh status

# 健康检查
curl --noproxy '*' http://localhost:8899/api/health

# 运行测试
pytest tests/ -v

# 端口检查
fuser 8899/tcp
```

---

## 🏗️ 项目结构

```text
model-switcher/
├── server.py               # Python 后端（多线程 HTTP + 多 profile API + CLI 切换）
├── index.html              # 前端页面（深色主题 + profile 联动 + 健康栏）
├── style.css               # 样式表（深色主题设计系统）
├── tests/
│   ├── __init__.py
│   └── test_server.py      # 16 单元测试
├── ctl.sh                  # 启停脚本（PORT 感知）
├── install.sh              # 一键安装（动态发现 python3/project dir）
├── model-switcher.service  # systemd user 单元模板
├── requirements.txt        # Python 依赖
└── README.md
```

---

## 🔐 安全

- 监听 `0.0.0.0:8899`，推荐内网/本机使用
- 外网访问请加反向代理 + 认证
- 不直接操作 API key（仅改动 `model.default` / `model.provider`）
- 静态文件路由含路径穿越守卫（`is_relative_to`）
- 当前会话不热切模型，**新会话**才生效

---

## 📋 版本历史

| 版本 | 日期 | 内容 |
|------|------|------|
| `v0.4.0` | 2026-05-12 | 生产加固：`ThreadingHTTPServer` 并发、CSS 分离 + 静态文件路由、16 单元测试、路径穿越守卫 |
| `v0.3.0` | 2026-05-12 | 多 Agent（profile）支持：profile 下拉联动、全 API 支持 `?profile=`、`POST /api/switch` 支持 `profile` 字段 |
| `v0.2.0` | 2026-05-12 | 通用版：动态发现 hermes、health 接口与回读校验、前端韧性（超时+重试+健康栏） |
| `v0.1.0` | 2026-05-11 | 首个可用版：Web 切换 + systemd 自启 + hermes CLI 切换 |

---

## ⚙️ 许可证

MIT
