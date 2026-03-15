# ✅ 正确的目录结构

## 📁 完整布局

```
pyclaw/                          # 项目根目录
│
├── scheduler/                   # 调度器代码模块
│   ├── heartbeat.py
│   └── __init__.py
│
├── sessions/                    # 会话管理代码模块
│   ├── manager.py
│   └── store.py
│
├── workspace/                   # 工作区（配置、数据、运行时文件）
│   ├── scheduler/               # ⚠️ 运行时创建（heartbeat.py）
│   │   └── heartbeat-state.json
│   │
│   ├── sessions/                # ⚠️ 运行时创建（store.py）
│   │   ├── sessions.json
│   │   └── <sessionId>.jsonl
│   │
│   ├── memory/                  # 记忆文件
│   │   ├── YYYY-MM-DD.md
│   │   └── 长期记忆.md
│   │
│   ├── skills-installed/        # 安装的技能
│   ├── vector_store/            # 向量存储
│   ├── config.json              # 主配置文件
│   └── *.md                     # 文档
│
├── agents/                      # Agent 代码
├── tools/                       # 工具代码
├── skills/                      # 技能代码模块
├── main.py                      # 主程序
└── ...
```

---

## 🎯 目录说明

### 1. scheduler/ (项目根目录)

**类型：** 代码模块

**内容：**
- `heartbeat.py` - 心跳调度器实现
- `__init__.py` - 模块初始化

**用途：** 实现心跳调度功能

---

### 2. workspace/scheduler/ (运行时创建)

**类型：** 运行时数据

**创建者：** `scheduler/heartbeat.py`

**内容：**
- `heartbeat-state.json` - 心跳状态

**代码引用：**
```python
# scheduler/heartbeat.py 第 105-106 行
self.workspace_path = Path.cwd() / "workspace"
self.state_path = Path(self.workspace_path / "scheduler" / "heartbeat-state.json")
```

---

### 3. sessions/ (项目根目录)

**类型：** 代码模块

**内容：**
- `manager.py` - 会话管理器
- `store.py` - 会话存储

**用途：** 实现会话管理功能

---

### 4. workspace/sessions/ (运行时创建)

**类型：** 运行时数据

**创建者：** `sessions/store.py`

**内容：**
- `sessions.json` - 会话索引
- `<sessionId>.jsonl` - 会话转录

**代码引用：**
```python
# sessions/store.py 第 99-100 行
self.store_dir = Path(
    store_dir or Path.cwd() / "workspace" / "sessions"
)
```

---

## 📊 代码 vs 数据

### 代码模块（项目根目录）

| 目录 | 用途 | 包含 |
|------|------|------|
| **scheduler/** | 调度器实现 | heartbeat.py |
| **sessions/** | 会话管理实现 | manager.py, store.py |
| **skills/** | 技能代码 | skill_loader.py |

### 运行时数据（workspace/）

| 目录 | 创建者 | 内容 |
|------|--------|------|
| **workspace/scheduler/** | heartbeat.py | heartbeat-state.json |
| **workspace/sessions/** | store.py | sessions.json, *.jsonl |
| **workspace/memory/** | 手动/自动 | *.md |
| **workspace/skills-installed/** | ClawHub/手动 | 技能目录 |

---

## ⚠️ 注意事项

### 1. 不要删除运行时目录

**workspace/scheduler/** 和 **workspace/sessions/** 会被自动创建，不要删除。

### 2. Git 忽略

建议在 `.gitignore` 中添加：
```gitignore
# 运行时数据
workspace/scheduler/
workspace/sessions/
workspace/vector_store/
workspace/__pycache__/
```

### 3. 备份

备份时应该包含：
```bash
# 包含配置和记忆
tar -czf backup.tar.gz workspace/
```

---

## 🔍 验证方法

### 检查目录是否存在

```bash
cd /home/zjm/.openclaw/workspace/pyclaw

# 代码模块
ls -la scheduler/ sessions/ skills/

# 运行时数据
ls -la workspace/scheduler/ workspace/sessions/ workspace/memory/
```

### 检查文件创建

```bash
# 启动 PyClaw 后
python3 main.py

# 检查是否创建运行时文件
ls -la workspace/scheduler/heartbeat-state.json
ls -la workspace/sessions/
```

---

## 📚 相关文件

- `scheduler/heartbeat.py` - 心跳调度器
- `sessions/store.py` - 会话存储
- `workspace/README.md` - 工作区说明

---

**目录结构说明完成！** 🎉

现在清楚了：
- ✅ scheduler/ 和 sessions/ 是代码模块（项目根目录）
- ✅ workspace/scheduler/ 和 workspace/sessions/ 是运行时数据（自动创建）

---

**最后更新：** 2026-03-14  
**状态：** ✅ 已修正
