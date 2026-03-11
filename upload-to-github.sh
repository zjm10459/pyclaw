#!/bin/bash
# PyClaw GitHub 上传脚本
# 使用方式：./upload-to-github.sh

set -e

echo "======================================"
echo " PyClaw GitHub 上传工具"
echo "======================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否在 git 仓库中
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}错误：当前目录不是 git 仓库${NC}"
    exit 1
fi

# 检查 Git 是否安装
if ! command -v git &> /dev/null; then
    echo -e "${RED}错误：Git 未安装${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Git 已安装${NC}"

# 获取用户名
echo ""
echo "请输入你的 GitHub 用户名："
read -p "> " GITHUB_USER

if [ -z "$GITHUB_USER" ]; then
    echo -e "${RED}错误：用户名不能为空${NC}"
    exit 1
fi

echo ""
echo "请选择仓库可见性："
echo "1) 公开仓库 (Public)"
echo "2) 私有仓库 (Private)"
read -p "> " VISIBILITY_CHOICE

if [ "$VISIBILITY_CHOICE" = "1" ]; then
    VISIBILITY="public"
elif [ "$VISIBILITY_CHOICE" = "2" ]; then
    VISIBILITY="private"
else
    echo -e "${RED}错误：无效选择${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}准备上传到：https://github.com/${GITHUB_USER}/pyclaw${NC}"
echo -e "${YELLOW}可见性：${VISIBILITY}${NC}"
echo ""
read -p "确认继续？(y/n): " CONFIRM

if [ "$CONFIRM" != "y" ]; then
    echo "已取消"
    exit 0
fi

# 检查是否配置了远程仓库
REMOTE_EXISTS=$(git remote | grep origin || true)

if [ -z "$REMOTE_EXISTS" ]; then
    echo ""
    echo -e "${YELLOW}未配置远程仓库，请选择配置方式：${NC}"
    echo "1) 使用 HTTPS"
    echo "2) 使用 SSH"
    read -p "> " REMOTE_CHOICE
    
    if [ "$REMOTE_CHOICE" = "1" ]; then
        REMOTE_URL="https://github.com/${GITHUB_USER}/pyclaw.git"
    elif [ "$REMOTE_CHOICE" = "2" ]; then
        REMOTE_URL="git@github.com:${GITHUB_USER}/pyclaw.git"
    else
        echo -e "${RED}错误：无效选择${NC}"
        exit 1
    fi
    
    echo ""
    echo "添加远程仓库..."
    git remote add origin $REMOTE_URL
    echo -e "${GREEN}✓ 远程仓库已添加${NC}"
else
    echo -e "${GREEN}✓ 远程仓库已配置${NC}"
fi

# 检查当前分支
CURRENT_BRANCH=$(git branch --show-current)
echo ""
echo "当前分支：${CURRENT_BRANCH}"

# 推送代码
echo ""
echo -e "${YELLOW}准备推送代码...${NC}"
echo ""

# 显示将要推送的文件
echo "将要推送的文件："
git status --short
echo ""

read -p "确认推送？(y/n): " PUSH_CONFIRM

if [ "$PUSH_CONFIRM" = "y" ]; then
    echo ""
    echo "推送到 GitHub..."
    
    # 尝试推送
    if git push -u origin ${CURRENT_BRANCH} 2>&1; then
        echo ""
        echo -e "${GREEN}======================================"
        echo " ✓ 上传成功！"
        echo -e "======================================${NC}"
        echo ""
        echo "仓库地址："
        echo "https://github.com/${GITHUB_USER}/pyclaw"
        echo ""
        echo "查看仓库状态："
        echo "git remote show origin"
        echo ""
    else
        echo ""
        echo -e "${RED}======================================"
        echo " ✗ 推送失败"
        echo -e "======================================${NC}"
        echo ""
        echo "可能的原因："
        echo "1. 远程仓库不存在 - 请先在 GitHub 上创建仓库"
        echo "2. 认证失败 - 请检查 SSH key 或 GitHub token"
        echo "3. 权限不足 - 请检查仓库权限"
        echo ""
        echo "手动创建仓库："
        echo "https://github.com/new"
        echo ""
        exit 1
    fi
else
    echo "已取消推送"
    exit 0
fi

echo ""
echo "完成！"
