# ✅ 运行时文件创建说明

## 📊 两个文件夹的文件创建时机

### 1. workspace/scheduler/

**创建者：** `scheduler/heartbeat.py`

**文件：** `heartbeat-state.json`

**创建时机：**
- ✅ 心跳任务**执行完成后**
- ✅ 默认间隔：**30 分钟**

**触发条件：**
```python
# 心跳任务执行完成后自动保存
async def _run_task(self, task):
    result = await task.handler()
    self._save_state()  # ← 这里保存
```

**为什么现在是空的：**
1. **心跳未启用** - config.json 中所有任务都是 `false`
2. **时间未到** - 即使启用，也要等 30 分钟后才执行第一次

**配置检查：**
```json
{
  "heartbeat": {
    "enable_email": false,      // ❌ 未启用
    "enable_calendar": false,   // ❌ 未启用
    "enable_weather": false,    // ❌ 未启用
    "default_interval_minutes": 30
  }
}
```

**如何启用：**
```json
{
  "heartbeat": {
    "enable_email": true,
    "enable_calendar": false,
    "enable_weather": false,
    "default_interval_minutes": 30
  }
}
```

---

### 2. workspace/sessions/

**创建者：** `sessions/store.py`

**文件：**
- `sessions.json` - 会话索引
- `<sessionId>.jsonl` - 会话转录

**创建时机：**
- ✅ **创建新会话时**
- ✅ **会话更新时**
- ✅ **会话结束时**

**触发条件：**
```python
# 创建会话时
def create(self, session_key: str):
    record = SessionRecord(...)
    self.sessions[session_key] = record
    self._save_index()  # ← 这里保存

# 更新会话时
def update(self, session_key: str, **kwargs):
    record = self.sessions[session_key]
    setattr(record, key, value)
    self._save_index()  # ← 这里保存
```

**为什么现在是空的：**
1. **使用内存存储** - 当前会话可能存储在内存中
2. **会话未持久化** - 可能使用了不同的存储后端
3. **刚启动** - 还没有创建/更新会话

---

## 🔍 验证方法

### 检查 heartbeat 是否运行

```bash
cd /home/zjm/.openclaw/workspace/pyclaw
python3 main.py --verbose 2>&1 | grep -i "heartbeat"
```

**预期输出：**
```
Heartbeat 调度器初始化：~/.pyclaw/workspace
已注册 0 个心跳任务
```

### 检查 sessions 是否使用

```bash
python3 main.py --verbose 2>&1 | grep -i "session"
```

**预期输出：**
```
会话管理器初始化完成
创建新会话：session_xxx
```

---

## ⏰ 文件创建时间线

### 启动时（0 分钟）

```
pyclaw 启动
├── 初始化 scheduler/ ✅
├── 初始化 sessions/ ✅
└── workspace/ 目录保持为空 ⚪
```

### 第一次心跳（30 分钟后，如果启用）

```
心跳任务触发
├── 执行任务（检查邮件/日历/天气）
├── 保存状态
└── workspace/scheduler/heartbeat-state.json ✅ 创建
```

### 创建会话时（立即）

```
用户发送消息
├── 创建新会话
├── 保存会话索引
└── workspace/sessions/sessions.json ✅ 创建
    workspace/sessions/<sessionId>.jsonl ✅ 创建
```

---

## 🎯 立即创建文件的方法

### 方法 1：启用心跳

**修改 config.json：**
```json
{
  "heartbeat": {
    "enable_email": true,
    "default_interval_minutes": 1  // 改为 1 分钟测试
  }
}
```

**重启 PyClaw：**
```bash
pkill -f "python.*main.py"
python3 main.py
```

**等待 1 分钟后检查：**
```bash
ls -la workspace/scheduler/
# 应该看到 heartbeat-state.json
```

---

### 方法 2：创建会话

**通过 pyclaw-web 发送消息：**
1. 打开 http://127.0.0.1:18800
2. 创建新会话
3. 发送一条消息

**检查文件：**
```bash
ls -la workspace/sessions/
# 应该看到 sessions.json 和会话文件
```

---

### 方法 3：手动触发

**测试 heartbeat：**
```bash
cd /home/zjm/.openclaw/workspace/pyclaw
python3 -c "
from scheduler.heartbeat import HeartbeatScheduler
from pathlib import Path

scheduler = HeartbeatScheduler(workspace=Path('workspace'))
scheduler._save_state()
print('✅ 状态已保存')
"

ls -la workspace/scheduler/
```

**测试 sessions：**
```bash
python3 -c "
from sessions.store import SessionStore
from pathlib import Path

store = SessionStore(store_dir=Path('workspace/sessions'))
store.create('test-session')
print('✅ 会话已创建')
"

ls -la workspace/sessions/
```

---

## 📊 当前状态

### workspace/scheduler/

| 状态 | 说明 |
|------|------|
| **目录存在** | ✅ 已创建 |
| **文件存在** | ❌ 未创建 |
| **原因** | 心跳任务未启用/时间未到 |

### workspace/sessions/

| 状态 | 说明 |
|------|------|
| **目录存在** | ✅ 已创建 |
| **文件存在** | ❌ 未创建 |
| **原因** | 会话可能存储在内存中/未持久化 |

---

## ⚠️ 注意事项

### 1. 心跳配置

**默认不启用任何任务：**
```json
{
  "heartbeat": {
    "enable_email": false,
    "enable_calendar": false,
    "enable_weather": false
  }
}
```

**需要手动启用。**

### 2. 会话存储

**可能使用不同的存储后端：**
- 内存存储（默认）
- 文件存储
- 数据库存储

**检查配置：**
```json
{
  "sessions": {
    "storage": "file"  // 或 "memory"
  }
}
```

### 3. 文件权限

**确保有写入权限：**
```bash
chmod -R 755 workspace/
```

---

## 📚 相关文件

- `scheduler/heartbeat.py` - 心跳调度器
- `sessions/store.py` - 会话存储
- `workspace/config.json` - 配置文件

---

**说明完成！** 🎉

现在你知道：
- ✅ 文件何时创建
- ✅ 为什么现在是空的
- ✅ 如何立即创建文件

---

**最后更新：** 2026-03-14  
**状态：** ✅ 已说明
