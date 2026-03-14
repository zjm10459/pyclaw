#!/bin/bash
# Email Sender Skill 安装脚本
# =============================

SKILL_NAME="email-sender"
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPENCLAW_SKILLS_DIR="$HOME/.openclaw/skills"

echo "📧 Email Sender Skill 安装脚本"
echo "=============================="
echo ""

# 检查 OpenClaw 目录
if [ ! -d "$HOME/.openclaw" ]; then
    echo "❌ 未找到 OpenClaw 目录：$HOME/.openclaw"
    echo "请先安装 OpenClaw"
    exit 1
fi

# 创建 skills 目录
mkdir -p "$OPENCLAW_SKILLS_DIR"

# 复制 Skill 文件
echo "📦 复制 Skill 文件..."
DEST_DIR="$OPENCLAW_SKILLS_DIR/$SKILL_NAME"

if [ -d "$DEST_DIR" ]; then
    echo "⚠️  目标目录已存在：$DEST_DIR"
    read -p "是否覆盖？[y/N] " confirm
    if [ "$confirm" != "y" ]; then
        echo "取消安装"
        exit 0
    fi
    rm -rf "$DEST_DIR"
fi

cp -r "$SKILL_DIR" "$DEST_DIR"

# 设置权限
chmod +x "$DEST_DIR"/*.py
chmod +x "$DEST_DIR"/*.sh
chmod 600 "$DEST_DIR"/*.json

echo "✓ Skill 已安装到：$DEST_DIR"
echo ""

# 测试安装
echo "🧪 测试安装..."
cd "$DEST_DIR"
python3 email_skill.py test

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 安装成功！"
    echo ""
    echo "使用方法："
    echo "  在 OpenClaw 中调用以下工具："
    echo "    - send_email(to=\"...\", subject=\"...\", body=\"...\")"
    echo "    - configure_email(provider=\"qq\", email=\"...\", password=\"...\")"
    echo "    - test_email(to=\"...\")"
    echo ""
    echo "首次使用请先配置邮箱："
    echo "  configure_email(provider=\"qq\", email=\"your@qq.com\", password=\"授权码\")"
    echo ""
else
    echo ""
    echo "⚠️  测试失败，请检查 Python 环境"
    exit 1
fi
