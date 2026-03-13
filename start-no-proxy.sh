#!/bin/bash
# PyClaw 启动脚本（禁用代理下载模型）

set -e

echo "🦮 PyClaw 启动脚本"
echo "=================="

# 临时禁用代理（用于下载 HuggingFace 模型）
NO_PROXY="*"
HTTPS_PROXY=""
HTTP_PROXY=""
HF_ENDPOINT=https://hf-mirror.com

export NO_PROXY HTTPS_PROXY HTTP_PROXY HF_ENDPOINT

echo "✓ 已禁用代理"
echo "✓ 使用镜像源：$HF_ENDPOINT"
echo ""

cd "$(dirname "$0")"

# 启动 Gateway
echo "🚀 启动 PyClaw Gateway..."
.venv/bin/python main.py --port 18790 --multi-agent
