#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSTEMD_DIR="$HOME/.config/systemd/user"
SERVICE_NAME="model-switcher.service"
SERVICE_SRC="$DIR/$SERVICE_NAME"
SERVICE_DST="$SYSTEMD_DIR/$SERVICE_NAME"
CONFIG_PATH="$HOME/.hermes/config.yaml"
PORT="${PORT:-8899}"

# ── preflight ──────────────────────────────────────────────────────

mkdir -p "$SYSTEMD_DIR"
chmod +x "$DIR/ctl.sh" "$DIR/install.sh"

if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ python3 未安装"
  exit 1
fi
PYTHON3="$(command -v python3)"

if ! "$PYTHON3" -c 'import yaml' >/dev/null 2>&1; then
  echo "❌ 缺少 pyyaml，请执行: pip install -r $DIR/requirements.txt"
  exit 1
fi

if ! command -v hermes >/dev/null 2>&1 && [ -z "${HERMES_BIN:-}" ]; then
  echo "❌ hermes CLI 未找到 (PATH 中无 hermes 且未设置 HERMES_BIN)"
  exit 1
fi

if [ ! -f "$CONFIG_PATH" ]; then
  echo "❌ Hermes 配置不存在: $CONFIG_PATH"
  exit 1
fi

if ! systemctl --user --version >/dev/null 2>&1; then
  echo "❌ 当前环境不支持 systemctl --user"
  exit 1
fi

if command -v fuser >/dev/null 2>&1; then
  if fuser "$PORT/tcp" >/dev/null 2>&1; then
    echo "⚠️  端口 $PORT 已被占用，请先检查: fuser $PORT/tcp"
    exit 1
  fi
fi

# ── generate service file from template ───────────────────────────

sed \
  -e "s|{{PROJECT_DIR}}|$DIR|g" \
  -e "s|{{PYTHON3}}|$PYTHON3|g" \
  "$SERVICE_SRC" > "$SERVICE_DST"

# ── install & start ───────────────────────────────────────────────

systemctl --user daemon-reload
systemctl --user enable --now "$SERVICE_NAME"

if ! curl --noproxy '*' -fsS "http://localhost:$PORT/api/health" >/dev/null 2>&1; then
  echo "⚠️  服务已启动，但健康检查失败，请执行: journalctl --user -u $SERVICE_NAME -f"
  exit 1
fi

echo "✅ 已安装并启动 model-switcher"
echo "   访问: http://localhost:$PORT"
echo "   健康检查: curl --noproxy '*' http://localhost:$PORT/api/health"
echo "   状态: systemctl --user status $SERVICE_NAME"
