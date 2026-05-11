#!/bin/bash
# Hermes Model Switcher — start/stop helper
DIR="$HOME/.hermes/model-switcher"
PIDFILE="$DIR/.pid"

case "${1:-start}" in
  start)
    if [ -f "$PIDFILE" ] && kill -0 $(cat "$PIDFILE") 2>/dev/null; then
      echo "⚠️  已经在运行中 (PID: $(cat $PIDFILE))"
      echo "   访问: http://localhost:8899"
      exit 0
    fi
    cd "$DIR"
    nohup python3 -u server.py > "$DIR/server.log" 2>&1 &
    echo $! > "$PIDFILE"
    sleep 1
    echo "🧠 Hermes Model Switcher 已启动"
    echo "   访问: http://localhost:8899"
    echo "   日志: $DIR/server.log"
    ;;
  stop)
    if [ -f "$PIDFILE" ]; then
      PID=$(cat "$PIDFILE")
      kill "$PID" 2>/dev/null && echo "✅ 已停止 (PID: $PID)"
      rm -f "$PIDFILE"
    else
      echo "⚠️  未在运行"
    fi
    ;;
  status)
    if [ -f "$PIDFILE" ] && kill -0 $(cat "$PIDFILE") 2>/dev/null; then
      echo "✅ 运行中 (PID: $(cat $PIDFILE)) → http://localhost:8899"
    else
      echo "❌ 未运行"
    fi
    ;;
  *)
    echo "用法: $0 {start|stop|status}"
    ;;
esac
