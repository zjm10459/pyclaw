# ✅ 最终目录结构

## 📁 目录布局

```
pyclaw/                          # 项目根目录
│
├── skills/                      # 技能代码模块（开发用）
│   ├── skill_loader.py          # 技能加载器
│   └── __pycache__/
│
├── workspace/                   # 工作区（配置、记忆、安装的技能）
│   ├── skills-installed/        # 安装的技能
│   │   ├── context7/
│   │   ├── email-sender/
│   │   ├── github/
│   │   └── ...
│   │
│   ├── memory/                  # 记忆文件
│   │   └── 2026-03-14.md
│   │
│   ├── config.json              # 主配置文件
│   ├── 人格记忆.md               # 人格定义
│   ├── AGENT.md                 # Agent 说明
│   ├── IDENTITY.md              # 身份定义
│   ├── USER.md                  # 用户信息
│   ├── TOOLS.md                 # 工具说明
│   ├── 长期记忆.md               # 长期记忆
│   └── README.md                # 工作区说明
│
├── agents/                      # Agent 实现代码
├── tools/                       # 工具实现代码
├── memory/                      # 记忆系统代码
├── main.py                      # 主程序
└── ...                          # 其他代码文件
```

---

## 🎯 目录说明

### 1. skills/ - 技能代码模块

**位置：** 项目根目录

**用途：**
- 开发自定义技能代码
- 存放技能加载器
- 技能核心实现

**文件：**
- `skill_loader.py` - 技能加载器
- `__pycache__/` - Python 缓存

---

### 2. workspace/ - 工作区

**位置：** 项目根目录

**用途：**
- 存放配置文件
- 存放记忆文件
- 存放安装的技能

**子目录：**

#### workspace/skills-installed/
- 安装的技能（从 ClawHub 或手动安装）
- 每个技能一个目录
- 包含 SKILL.md 和实现代码

#### workspace/memory/
- 每日记忆文件（YYYY-MM-DD.md）
- 记录当天的对话和事件

---

### 3. workspace/ 根目录文件

| 文件 | 用途 |
|------|------|
| **config.json** | PyClaw 主配置文件 |
| **人格记忆.md** | Agent 人格定义 |
| **AGENT.md** | Agent 工作区说明 |
| **IDENTITY.md** | Agent 身份定义 |
| **USER.md** | 用户信息 |
| **TOOLS.md** | 工具配置说明 |
| **长期记忆.md** | 长期记忆（精选内容） |
| **README.md** | 工作区使用说明 |

---

## 🔧 代码引用

### 工作区路径

```python
from pathlib import Path

# 工作区路径
workspace_path = Path(__file__).parent / "workspace"

# 技能代码路径（项目根目录）
skills_path = Path(__file__).parent / "skills"

# 安装的技能路径
skills_installed = workspace_path / "skills-installed"

# 记忆文件路径
memory_dir = workspace_path / "memory"
long_term_memory = workspace_path / "长期记忆.md"
```

---

## 📊 文件分类

### 代码文件（不纳入工作区）

- ✅ `agents/` - Agent 实现
- ✅ `tools/` - 工具实现
- ✅ `memory/` - 记忆系统代码
- ✅ `skills/` - 技能代码模块
- ✅ `main.py` - 主程序

### 数据和配置（纳入工作区）

- ✅ `workspace/config.json` - 配置
- ✅ `workspace/*.md` - 人格、用户信息
- ✅ `workspace/memory/` - 记忆文件
- ✅ `workspace/skills-installed/` - 安装的技能

---

## 🎯 使用方式

### 开发自定义技能

```bash
cd /home/zjm/.openclaw/workspace/pyclaw
cd skills
vim my_skill.py
```

### 安装技能

```bash
cd /home/zjm/.openclaw/workspace/pyclaw
clawhub install skill-name
# 自动安装到 workspace/skills-installed/
```

### 查看记忆

```bash
cd /home/zjm/.openclaw/workspace/pyclaw
cd workspace/memory
cat 2026-03-14.md
cat ../长期记忆.md
```

### 修改配置

```bash
cd /home/zjm/.openclaw/workspace/pyclaw
cd workspace
vim config.json
vim USER.md
```

---

## ✅ 优势

### 1. 代码和数据分离

**代码：** `agents/`, `tools/`, `skills/`
**数据：** `workspace/`

### 2. 便于版本控制

**Git 管理代码：**
```bash
git add agents/ tools/ skills/ main.py
```

**Git 忽略数据（可选）：**
```bash
echo "workspace/" >> .gitignore
```

### 3. 便于备份

**备份工作区：**
```bash
tar -czf workspace-backup.tar.gz workspace/
```

### 4. 结构清晰

- 代码在根目录
- 配置和数据在 workspace/
- 技能代码在 skills/
- 安装的技能在 workspace/skills-installed/

---

## ⚠️ 注意事项

### 1. 路径引用

**使用相对路径：**
```python
# ✅ 正确
workspace_path = Path(__file__).parent / "workspace"

# ❌ 错误（硬编码）
workspace_path = Path("/home/zjm/.openclaw/workspace/pyclaw/workspace")
```

### 2. 技能加载

**技能加载器会自动查找：**
```python
skill_dirs = [
    workspace.parent / "skills",         # 项目根目录 skills/
    workspace / "skills-installed",      # workspace/skills-installed/
    ...
]
```

### 3. 配置文件

**config.json 现在在 workspace/ 下：**
```bash
cd workspace
vim config.json
```

---

## 📚 相关文档

- `workspace/README.md` - 工作区使用说明
- `docs/WORKSPACE_REFACTORING.md` - 重构说明
- `docs/TOOLS_CLEANUP.md` - tools 文件夹清理
- `docs/SKILL_HOTPLUG.md` - 技能热插拔

---

**目录结构优化完成！** 🎉

现在：
- ✅ 代码和数据分离
- ✅ 结构清晰
- ✅ 便于维护
- ✅ 便于版本控制

---

**最后更新：** 2026-03-14  
**状态：** ✅ 已完成
