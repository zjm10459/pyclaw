# PyClaw GitHub 上传指南

## 方法一：使用 GitHub CLI（推荐）

### 1. 安装 GitHub CLI

```bash
# Ubuntu/Debian
sudo apt install gh

# macOS
brew install gh

# 或者使用 pip
pip install gh
```

### 2. 登录 GitHub

```bash
gh auth login
```

按照提示：
- 选择 GitHub.com
- 选择 HTTPS
- 复制 One-Time Code
- 在浏览器中完成认证

### 3. 创建仓库

```bash
cd /home/zjm/.openclaw/workspace/pyclaw

# 创建新仓库（私有）
gh repo create pyclaw --private --source=. --remote=origin

# 或者创建公开仓库
gh repo create pyclaw --public --source=. --remote=origin
```

### 4. 推送代码

```bash
git push -u origin master
```

---

## 方法二：使用 Git 命令

### 1. 在 GitHub 上创建仓库

访问 https://github.com/new

- **Repository name:** pyclaw
- **Description:** OpenClaw 的 Python 实现 - 基于 LangGraph 的多 Agent 协作系统
- **Visibility:** Private 或 Public
- **不要** 初始化 README（我们已经有代码了）

### 2. 添加远程仓库

```bash
cd /home/zjm/.openclaw/workspace/pyclaw

# 添加远程仓库（替换为你的用户名）
git remote add origin https://github.com/YOUR_USERNAME/pyclaw.git

# 或者使用 SSH（推荐）
git remote add origin git@github.com:YOUR_USERNAME/pyclaw.git
```

### 3. 推送代码

```bash
# 推送到 master 分支
git push -u origin master
```

---

## 方法三：使用 Git 客户端工具

### GitHub Desktop

1. 下载：https://desktop.github.com
2. 登录 GitHub 账号
3. File → Add Local Repository → 选择 `pyclaw` 文件夹
4. Publish repository

### Sourcetree

1. 下载：https://www.sourcetreeapp.com
2. 添加现有仓库
3. 推送到 GitHub

---

## 验证上传

### 1. 查看仓库

访问：https://github.com/YOUR_USERNAME/pyclaw

### 2. 检查文件

确保以下文件已上传：
- ✅ README.md
- ✅ pyproject.toml
- ✅ main.py
- ✅ agents/
- ✅ memory/
- ✅ tools/
- ✅ tests/

### 3. 检查忽略的文件

确保以下文件**没有**被上传：
- ❌ __pycache__/
- ❌ *.pyc
- ❌ .env
- ❌ uv.lock
- ❌ *.log

---

## 配置 SSH（推荐）

### 1. 生成 SSH Key

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

### 2. 添加到 GitHub

```bash
# 复制公钥
cat ~/.ssh/id_ed25519.pub | xclip -selection clipboard

# 访问：https://github.com/settings/keys
# 点击 "New SSH key"
# 粘贴公钥
```

### 3. 测试连接

```bash
ssh -T git@github.com
```

---

## 更新代码

### 日常开发流程

```bash
# 1. 修改代码
# ...

# 2. 查看状态
git status

# 3. 添加更改
git add .

# 4. 提交
git commit -m "feat: 添加新功能"

# 5. 推送
git push origin master
```

### 查看提交历史

```bash
git log --oneline
```

---

## 分支管理

### 创建新分支

```bash
# 创建并切换分支
git checkout -b feature/new-feature

# 推送分支
git push -u origin feature/new-feature
```

### 合并分支

```bash
# 切换回 master
git checkout master

# 合并分支
git merge feature/new-feature

# 推送到远程
git push origin master
```

---

## 添加贡献者

### 1. 邀请贡献者

访问：https://github.com/YOUR_USERNAME/pyclaw/settings/access

点击 "Invite a collaborator"

### 2. 设置权限

- **Read** - 只读
- **Write** - 可推送
- **Admin** - 完全权限

---

## 使用 GitHub Actions（可选）

### 创建 CI/CD 工作流

创建 `.github/workflows/ci.yml`:

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -e ".[dev]"
    
    - name: Run tests
      run: |
        pytest tests/ -v --cov=pyclaw
```

---

## 常见问题

### Q: 推送失败：Permission denied

**A:** 检查 SSH key 是否配置正确
```bash
ssh -T git@github.com
```

### Q: 仓库太大

**A:** 使用 Git LFS 管理大文件
```bash
git lfs install
git lfs track "*.bin"
```

### Q: 如何删除远程仓库

**A:** 
```bash
# 删除远程分支
git push origin --delete branch-name

# 删除整个仓库（在 GitHub 设置中）
# Settings → Delete this repository
```

---

## 快速命令参考

```bash
# 查看远程仓库
git remote -v

# 添加远程仓库
git remote add origin git@github.com:USER/pyclaw.git

# 推送
git push -u origin master

# 拉取
git pull origin master

# 查看状态
git status

# 查看日志
git log --oneline

# 撤销提交
git reset HEAD~1
```

---

_创建时间：2026-03-11_
_PyClaw Team_
