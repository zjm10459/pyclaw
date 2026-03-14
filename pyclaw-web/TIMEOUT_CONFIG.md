# PyClaw Web 超时配置

## 📊 超时时间设置

### 前端（浏览器）

**文件：** `templates/index.html`

**超时时间：** 300 秒（5 分钟）

```javascript
// 创建带超时的 AbortController
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 分钟超时

const response = await fetch('/api/chat', {
    method: 'POST',
    signal: controller.signal,
    ...
});

clearTimeout(timeoutId);
```

**超时错误处理：**
```javascript
if (error.name === 'AbortError') {
    appendMessage('assistant', '错误：请求超时（5 分钟），任务可能仍在执行中。请稍后查看会话列表。');
}
```

---

### 后端（Python）

**文件：** `app/main.py`

**超时时间：** 300 秒（5 分钟）

```python
@app.post("/api/chat")
async def chat(chat_msg: ChatMessage):
    # 增加超时时间到 5 分钟（300 秒），支持多 Agent 等长时间任务
    response = await asyncio.wait_for(
        gateway_client.send_message(...),
        timeout=300.0,  # 5 分钟超时
    )
```

**超时错误处理：**
```python
except asyncio.TimeoutError:
    return ChatResponse(
        success=False,
        message="错误：请求超时（5 分钟），任务可能仍在执行中。请稍后查看会话列表。",
    )
```

---

## ⏱️ 超时时间对比

| 组件 | 修改前 | 修改后 | 提升 |
|------|--------|--------|------|
| **前端 fetch** | 默认（约 30 秒） | 300 秒 | +900% |
| **后端 asyncio** | 120 秒 | 300 秒 | +150% |
| **WebSocket ping** | - | 20 秒 | 新增 |
| **WebSocket close** | - | 10 秒 | 新增 |

---

## 🎯 适用场景

### 5 分钟超时适合：

✅ **多 Agent 协作** - 6 个角色完整执行约 60-90 秒
✅ **复杂搜索** - 多次工具调用和信息整理
✅ **代码生成** - 编写和调试复杂代码
✅ **文档撰写** - 长篇文档创作
✅ **数据分析** - 大量数据处理

### 可能需要更长超时：

⚠️ **批量任务** - 处理数十个文件
⚠️ **视频分析** - 处理大文件
⚠️ **模型训练** - 本地微调

---

## 🔧 调整超时时间

### 前端调整

编辑 `templates/index.html`：

```javascript
// 修改超时时间（毫秒）
const timeoutId = setTimeout(() => controller.abort(), 300000); // 300000 = 5 分钟

// 改为 10 分钟：
const timeoutId = setTimeout(() => controller.abort(), 600000); // 600000 = 10 分钟
```

### 后端调整

编辑 `app/main.py`：

```python
# 修改超时时间（秒）
response = await asyncio.wait_for(
    gateway_client.send_message(...),
    timeout=300.0,  # 300 秒 = 5 分钟

# 改为 10 分钟：
    timeout=600.0,  # 600 秒 = 10 分钟
)
```

---

## 📊 任务执行时间估算

| 任务类型 | 预计时间 | 超时设置 |
|---------|---------|---------|
| **简单问答** | 5-10 秒 | ✅ 远小于 5 分钟 |
| **单 Agent 工具调用** | 10-30 秒 | ✅ 远小于 5 分钟 |
| **多 Agent（3 角色）** | 30-60 秒 | ✅ 小于 5 分钟 |
| **多 Agent（6 角色）** | 60-120 秒 | ✅ 小于 5 分钟 |
| **复杂研究任务** | 2-4 分钟 | ✅ 小于 5 分钟 |
| **批量处理** | 5-10 分钟 | ⚠️ 可能需要更长 |

---

## ⚠️ 注意事项

### 1. 超时 vs 实际执行

**重要：** 前端超时后，后端任务可能仍在执行！

```
用户发送请求
    ↓
前端等待响应（5 分钟）
    ↓
如果超时 → 显示错误消息
    ↓
但后端 Gateway 仍在执行任务
    ↓
任务完成后结果会保存到会话
    ↓
用户可以在会话列表中查看结果
```

**建议：**
- 超时后不要重复提交相同请求
- 稍后查看会话列表获取结果

### 2. Gateway 超时

PyClaw Gateway 也有自己的超时设置：

**配置文件：** `~/.pyclaw/config.json` 或 `pyclaw/config.json`

```json
{
  "agents": {
    "defaults": {
      "max_iterations": 10,  // 最大迭代次数
      "timeout_seconds": 600  // Agent 超时（10 分钟）
    }
  }
}
```

**确保：** Gateway 超时 > Web 超时

### 3. 负载均衡器超时

如果使用 Nginx 等反向代理：

**Nginx 配置：**
```nginx
location /api/ {
    proxy_read_timeout 300s;  # 至少 5 分钟
    proxy_send_timeout 300s;
}
```

---

## 🔍 调试超时问题

### 查看日志

**前端：**
```javascript
// 在浏览器 Console 中查看
console.log('发送请求...');
// 如果看到 "AbortError"，说明前端超时
```

**后端：**
```bash
# 查看 pyclaw-web 日志
tail -f pyclaw-web.log | grep "超时\|timeout"

# 查看 Gateway 日志
tail -f pyclaw.log | grep "超时\|timeout"
```

### 测试超时

**快速测试：**
```javascript
// 临时设置为 1 秒测试超时
const timeoutId = setTimeout(() => controller.abort(), 1000);
```

---

## 📚 相关文件

- `pyclaw-web/templates/index.html` - 前端超时设置
- `pyclaw-web/app/main.py` - 后端超时设置
- `pyclaw/agents/langgraph_agent.py` - Agent 超时设置
- `pyclaw/config.json` - Gateway 超时设置

---

## 💡 最佳实践

### 1. 分层超时

```
前端超时（5 分钟） < Gateway 超时（10 分钟） < 模型超时（15 分钟）
```

### 2. 用户提示

超时后显示友好提示：
```
"错误：请求超时（5 分钟），任务可能仍在执行中。
请稍后查看会话列表获取结果。"
```

### 3. 异步任务

对于超长任务，考虑异步处理：
```
提交任务 → 立即返回任务 ID → 轮询结果
```

---

**更新时间：** 2026-03-14  
**状态：** ✅ 已配置 5 分钟超时
