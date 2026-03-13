#!/bin/bash
# PyClaw 启动脚本（带中文模型优化）

set -e

echo "🦮 PyClaw 启动脚本"
echo "=================="

# 设置 HuggingFace 镜像源（使用 BGE 中文模型）
export HF_ENDPOINT=https://hf-mirror.com
echo "✓ 设置镜像源：HF_ENDPOINT=$HF_ENDPOINT"

# 设置模型缓存目录（可选）
# export HF_HOME=~/.cache/huggingface

# 进入工作目录
cd "$(dirname "$0")"

echo ""
echo "📦 模型信息："
echo "   嵌入模型：BAAI/bge-small-zh-v1.5 (中文优化)"
echo "   模型大小：约 130MB"
echo "   向量维度：512"
echo ""

# 检查是否已有缓存
if [ -d ~/.cache/huggingface/hub/models--BAAI--bge-small-zh-v1.5 ]; then
    echo "✓ 模型已缓存，直接启动"
else
    echo "⚠️  首次启动，将自动下载模型（约 130MB）..."
    echo "   下载源：hf-mirror.com (国内镜像)"
    echo ""
fi

# 启动 Gateway
echo "🚀 启动 PyClaw Gateway..."
python3 main.py --port 18790 --multi-agent
