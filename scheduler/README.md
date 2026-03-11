# Scheduler 模块

Heartbeat 定时任务调度器。

## 文件说明

| 文件 | 说明 | 行数 |
|------|------|------|
| `heartbeat.py` | Heartbeat 调度器 | 350+ |

## 使用方式

### 基础使用

```python
from scheduler import create_heartbeat_scheduler

scheduler = create_heartbeat_scheduler(
    enable_email=True,
    enable_calendar=True,
)

await scheduler.start()
```

### 注册自定义任务

```python
from scheduler import HeartbeatScheduler

scheduler = HeartbeatScheduler()

async def my_task():
    print("执行任务...")
    return {"status": "done"}

scheduler.register_task(
    name="my_task",
    handler=my_task,
    interval_minutes=60,
)

await scheduler.start()
```

## 配置

### config.json

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

## HEARTBEAT.md

在工作区创建 `HEARTBEAT.md` 定义任务：

```markdown
# HEARTBEAT.md

# 定期检查任务
email
calendar
weather
```

## 预定义任务

- `check_email_handler` - 检查邮件
- `check_calendar_handler` - 检查日历
- `check_weather_handler` - 检查天气

## 状态追踪

状态文件：`~/.pyclaw/scheduler/heartbeat-state.json`

```json
{
  "last_updated": "2026-03-11T12:00:00",
  "tasks": {
    "email": {
      "last_run": "2026-03-11T12:00:00",
      "next_run": "2026-03-11T12:30:00",
      "enabled": true
    }
  }
}
```

## 文档

- `HEARTBEAT_SCHEDULER.md` - 完整文档
