# PyClaw 工作区

## 📁 目录结构

```
pyclaw/                          # 项目根目录
├── skills/                      # 技能代码模块（开发用）
│   └── (空目录)
│
└── workspace/                   # 工作区
    ├── skills-installed/        # 安装的技能
│   ├── context7/
│   ├── email-sender/
│   ├── github/
│   ├── github-trending-cn/
│   ├── multi-search-engine/
│   └── tavily-search/
│
├── memory/                  # 记忆文件
│   ├── 2026-03-14.md        # 每日记忆
│   └── (其他每日记忆文件)
│
├── config.json              # 主配置文件
├── 人格记忆.md               # 人格定义
├── AGENT.md                 # Agent 说明
├── IDENTITY.md              # 身份定义
├── USER.md                  # 用户信息
├── TOOLS.md                 # 工具说明
├── 长期记忆.md               # 长期记忆
└── docs/                    # 工作区文档
```

---

## 🎯 文件说明

### 技能相关

| 目录 | 用途 | 位置 |
|------|------|------|
| **skills/** | 技能代码模块（开发自定义技能） | 项目根目录 |
| **skills-installed/** | 安装的技能（从 ClawHub 或手动安装） | workspace/ |

### 记忆相关

| 文件 | 用途 |
|------|------|
| **memory/YYYY-MM-DD.md** | 每日记忆（原始日志） |
| **长期记忆.md** | 长期记忆（精选内容） |

### 配置相关

| 文件 | 用途 |
|------|------|
| **config.json** | PyClaw 主配置文件 |
| **人格记忆.md** | Agent 人格定义 |
| **AGENT.md** | Agent 工作区说明 |
| **IDENTITY.md** | Agent 身份定义 |
| **USER.md** | 用户信息 |
| **TOOLS.md** | 工具配置说明 |

---

## 🚀 使用方式

### 添加自定义技能

```bash
cd ..  # 返回项目根目录
cd skills
mkdir my-skill
cd my-skill
# 创建 SKILL.md 和技能代码
```

### 查看记忆文件

```bash
cd workspace/memory
cat 2026-03-14.md
cat ../长期记忆.md
```

### 修改配置

```bash
cd workspace
vim config.json
vim USER.md
```

---

## 📊 路径说明

**工作区路径：** `/home/zjm/.openclaw/workspace/pyclaw/workspace`
**技能代码路径：** `/home/zjm/.openclaw/workspace/pyclaw/skills`

**代码中引用：**
```python
from pathlib import Path

# 工作区路径
workspace_path = Path(__file__).parent / "workspace"

# 技能目录（在项目根目录）
skills_dir = Path(__file__).parent / "skills"
skills_installed = workspace_path / "skills-installed"

# 记忆目录
memory_dir = workspace_path / "memory"
long_term_memory = workspace_path / "长期记忆.md"
```

---

## ⚠️ 注意事项

1. **不要删除** - 工作区包含所有配置和记忆数据
2. **定期备份** - 建议定期备份整个 workspace 目录
3. **Git 管理** - 建议将 workspace 纳入版本控制（敏感信息除外）
4. **路径引用** - 代码中使用相对路径引用 workspace

---

## 🔗 相关文档

- `../docs/WORKSPACE_REFACTORING.md` - 工作区重构说明
- `../docs/SKILL_HOTPLUG.md` - 技能热插拔
- `../docs/MEMORY_TOOL_SETUP.md` - 记忆系统使用

---

**最后更新：** 2026-03-14  
**状态：** ✅ 已重构
