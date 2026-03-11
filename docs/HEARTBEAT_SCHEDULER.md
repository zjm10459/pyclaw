# Heartbeat 定时任务系统

## 概述

参考 OpenClaw 的 Heartbeat 设计，为 PyClaw 添加定时任务调度功能。

**核心功能：**
- ✅ 定时触发任务（类似 cron）
- ✅ HEARTBEAT.md 配置文件
- ✅ 任务状态追踪
- ✅ 支持多种任务类型（邮件检查、日历提醒、天气检查等）

---

## OpenClaw 的定时任务实现

OpenClaw 使用两种方式实现定时任务：

### 1. Heartbeat（心跳）

**适用场景：**
- 多个检查可以批量处理（邮箱 + 日历 + 通知）
- 需要最近消息的对话上下文
- 时间可以略有偏差（每 ~30 分钟，不需要精确）
- 想通过合并定期检查减少 API 调用

**实现方式：**
- 通过 `HEARTBEAT.md` 配置文件定义任务
- 默认心跳提示：`Read HEARTBEAT.md if it exists...`
- Agent 收到心跳轮询时执行任务
- 状态追踪在 `memory/heartbeat-state.json`

### 2. Cron（精确调度）

**适用场景：**
- 精确时间很重要（"每周一上午 9:00"）
- 任务需要与主会话历史隔离
- 想为任务使用不同的模型或思考级别
- 一次性提醒（"20 分钟后提醒我"）
- 输出应直接发送到渠道而不需要主会话参与

**实现方式：**
- 使用 `croner` 库（Node.js cron 实现）
- 支持 cron 表达式
- 独立于主会话执行

---

## PyClaw 实现

### 架构

```
HEARTBEAT.md → 解析任务配置 → HeartbeatScheduler → 执行任务 → 记录状态
```

### 文件结构

```
pyclaw/scheduler/
├── __init__.py          # 模块导出
└── heartbeat.py         # Heartbeat 调度器实现
```

### 核心类

#### HeartbeatScheduler

```python
from scheduler import HeartbeatScheduler

scheduler = HeartbeatScheduler(
    workspace_path="~/.pyclaw/workspace",
    state_path="~/.pyclaw/scheduler/heartbeat-state.json",
)
```

#### HeartbeatTask

```python
@dataclass
class HeartbeatTask:
    name: str                  # 任务名称
    interval_minutes: int      # 执行间隔（分钟）
    last_run: datetime         # 上次执行时间
    next_run: datetime         # 下次执行时间
    enabled: bool              # 是否启用
    handler: Callable          # 处理函数
```

---

## 使用方式

### 1. 基本使用

```python
from scheduler import create_heartbeat_scheduler

# 创建调度器
scheduler = create_heartbeat_scheduler(
    workspace_path="~/.pyclaw/workspace",
    enable_email=True,
    enable_calendar=True,
    enable_weather=True,
)

# 启动调度器
await scheduler.start()

# 停止调度器
await scheduler.stop()
```

### 2. 注册自定义任务

```python
from scheduler import HeartbeatScheduler

scheduler = HeartbeatScheduler()

# 注册任务
async def my_custom_task():
    print("执行自定义任务...")
    return {"status": "completed"}

scheduler.register_task(
    name="custom_task",
    handler=my_custom_task,
    interval_minutes=60,  # 每 60 分钟执行一次
    enabled=True,
)

await scheduler.start()
```

### 3. 配置 HEARTBEAT.md

在工作区创建 `HEARTBEAT.md`：

```markdown
# HEARTBEAT.md

# 定期检查任务（每行一个）
email
calendar
weather
github_notifications
```

### 4. 配置文件

在 `~/.pyclaw/config.json` 中添加：

```json
{
  "heartbeat": {
    "enable_email": true,
    "enable_calendar": true,
    "enable_weather": false,
    "default_interval_minutes": 30
  }
}
```

---

## 预定义任务处理器

### check_email_handler

检查新邮件。

```python
async def check_email_handler() -> Dict[str, Any]:
    """检查邮件示例处理器"""
    logger.info("检查新邮件...")
    # TODO: 实现邮件检查逻辑
    return {"status": "checked", "new_emails": 0}
```

### check_calendar_handler

检查日历事件。

```python
async def check_calendar_handler() -> Dict[str, Any]:
    """检查日历事件示例处理器"""
    logger.info("检查日历事件...")
    # TODO: 实现日历检查逻辑
    return {"status": "checked", "upcoming_events": []}
```

### check_weather_handler

检查天气。

```python
async def check_weather_handler() -> Dict[str, Any]:
    """检查天气示例处理器"""
    logger.info("检查天气...")
    # TODO: 实现天气检查逻辑
    return {"status": "checked", "weather": "sunny"}
```

---

## 状态追踪

### 状态文件

`~/.pyclaw/scheduler/heartbeat-state.json`

```json
{
  "last_updated": "2026-03-11T11:00:00",
  "tasks": {
    "email": {
      "name": "email",
      "interval_minutes": 30,
      "last_run": "2026-03-11T11:00:00",
      "next_run": "2026-03-11T11:30:00",
      "enabled": true
    },
    "calendar": {
      "name": "calendar",
      "interval_minutes": 60,
      "last_run": "2026-03-11T10:00:00",
      "next_run": "2026-03-11T11:00:00",
      "enabled": true
    }
  }
}
```

### 获取状态

```python
status = scheduler.get_status()
print(json.dumps(status, indent=2))
```

输出：
```json
{
  "running": true,
  "task_count": 2,
  "tasks": {
    "email": {
      "last_run": "2026-03-11T11:00:00",
      "next_run": "2026-03-11T11:30:00",
      "enabled": true,
      "interval_minutes": 30
    },
    "calendar": {
      "last_run": "2026-03-11T10:00:00",
      "next_run": "2026-03-11T11:00:00",
      "enabled": true,
      "interval_minutes": 60
    }
  }
}
```

---

## 集成到 main.py

### 自动启动

`main.py` 已集成 Heartbeat 调度器：

```python
# 初始化
await self._init_heartbeat_scheduler()

# 启动
if self.heartbeat_scheduler:
    await self.heartbeat_scheduler.start()
```

### 启动选项

```bash
# 默认启动（包含 Heartbeat）
python main.py

# 详细模式（查看 Heartbeat 日志）
python main.py --verbose
```

### 启动信息

```
🦮 ============================================================
🦮  PyClaw Gateway (LangGraph + 多 Agent 协作)
🦮 ============================================================
   监听地址：ws://127.0.0.1:18790
   ...
   Heartbeat 调度器：✓ 已启动
```

---

## 最佳实践

### Heartbeat vs Cron

| 特性 | Heartbeat | Cron |
|------|-----------|------|
| 时间精度 | 低（~30 分钟） | 高（精确到分钟） |
| 上下文 | 有对话上下文 | 独立执行 |
| API 调用 | 批量处理 | 单独调用 |
| 适用场景 | 定期检查 | 精确调度 |

### 建议

1. **使用 Heartbeat 当：**
   - 多个检查可以批量处理
   - 时间不需要很精确
   - 想减少 API 调用

2. **使用 Cron 当：**
   - 需要精确时间
   - 任务需要隔离
   - 一次性提醒

### 任务设计

```python
# ✅ 好的任务设计
async def check_email():
    """检查新邮件并通知"""
    emails = await get_new_emails()
    if emails:
        await notify_user(emails)
    return {"new_emails": len(emails)}

# ❌ 避免长时间运行的任务
async def bad_task():
    """不要这样做"""
    await asyncio.sleep(3600)  # 阻塞 1 小时
```

---

## 扩展示例

### 添加 GitHub 通知检查

```python
async def check_github_notifications():
    """检查 GitHub 通知"""
    import aiohttp
    
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.github.com/notifications",
            headers={"Authorization": f"token {GITHUB_TOKEN}"}
        ) as response:
            notifications = await response.json()
    
    if notifications:
        logger.info(f"GitHub 通知：{len(notifications)} 条")
    
    return {"notifications": len(notifications)}

# 注册任务
scheduler.register_task(
    name="github",
    handler=check_github_notifications,
    interval_minutes=30,
)
```

### 添加股票价格检查

```python
async def check_stock_price():
    """检查股票价格"""
    # TODO: 实现股票价格检查
    return {"stocks": {"AAPL": 150.00}}

scheduler.register_task(
    name="stocks",
    handler=check_stock_price,
    interval_minutes=15,  # 每 15 分钟检查一次
)
```

---

## 故障排查

### 问题 1: 调度器未启动

**症状：**
```
Heartbeat 调度器：✗ 未启动
```

**解决方案：**
1. 检查配置文件是否存在
2. 查看详细日志：`python main.py --verbose`
3. 确认 `scheduler/` 目录存在

### 问题 2: 任务未执行

**症状：**
```
last_run: null
next_run: null
```

**解决方案：**
1. 检查任务是否启用：`enabled: true`
2. 检查 `next_run` 时间是否正确
3. 查看日志中的错误信息

### 问题 3: 状态文件损坏

**症状：**
```
加载状态失败：JSONDecodeError
```

**解决方案：**
1. 删除状态文件：`rm ~/.pyclaw/scheduler/heartbeat-state.json`
2. 重启调度器（会自动创建新文件）

---

## 参考

- [OpenClaw HEARTBEAT.md](../HEARTBEAT.md)
- [OpenClaw AGENTS.md](../AGENTS.md) - Heartbeat 部分
- [croner 库文档](https://github.com/hexagon/croner) - Node.js cron 实现

---

_创建时间：2026-03-11_
_PyClaw Team_
