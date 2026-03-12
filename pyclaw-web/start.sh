#!/bin/bash
# PyClaw Web 启动脚本

set -e

echo "🦮 PyClaw Web 启动脚本"
echo "===================="
echo ""

# 使用 pyclaw 的虚拟环境
PYCLAW_VENV="$(dirname "$0")/../pyclaw/.venv"
PYTHON_BIN="$PYCLAW_VENV/bin/python"

if [ ! -f "$PYTHON_BIN" ]; then
    echo "❌ 错误：pyclaw 虚拟环境不存在"
    echo "请确保 pyclaw 已正确安装"
    exit 1
fi

# 设置环境变量
export PYCLAW_WEB_HOST=${PYCLAW_WEB_HOST:-"127.0.0.1"}
export PYCLAW_WEB_PORT=${PYCLAW_WEB_PORT:-"18800"}
export PYCLAW_GATEWAY_URL=${PYCLAW_GATEWAY_URL:-"ws://127.0.0.1:18790"}

echo "✅ 准备启动"
echo ""
echo "   Web 界面：http://${PYCLAW_WEB_HOST}:${PYCLAW_WEB_PORT}"
echo "   Gateway:  ${PYCLAW_GATEWAY_URL}"
echo ""
echo "   按 Ctrl+C 停止"
echo ""

# 启动应用
cd "$(dirname "$0")"
exec "$PYTHON_BIN" -m uvicorn app.main:app --host ${PYCLAW_WEB_HOST} --port ${PYCLAW_WEB_PORT}
