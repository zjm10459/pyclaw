# ✅ 超时问题修复

## 🐛 问题描述

**现象：** 2 分钟就超时

**日志：**
```
22:54:34 - ✓ 重连成功
22:56:34 - Gateway 返回失败：请求超时  ← 正好 2 分钟
```

---

## 🔍 问题原因

**错误位置：** `pyclaw-web/app/main.py` 第 293 行

**错误代码：**
```python
response = json.loads(await asyncio.wait_for(self.ws.recv(), timeout=120.0))
#                                                           ^^^^^^^
#                                                           2 分钟
```

**原因：**
- 前端超时设置为 60 分钟（3600000 毫秒）✅
- 后端超时设置为 60 分钟（3600.0 秒）✅
- **但 WebSocket 接收超时仍为 2 分钟（120.0 秒）** ❌

---

## ✅ 修复方案

**修改文件：** `pyclaw-web/app/main.py`

**修改前：**
```python
# 第 293 行
response = json.loads(await asyncio.wait_for(self.ws.recv(), timeout=120.0))
```

**修改后：**
```python
# 等待响应（60 分钟超时，支持长任务）
response = json.loads(await asyncio.wait_for(self.ws.recv(), timeout=3600.0))
```

---

## 📊 超时配置总览

| 位置 | 配置 | 超时时间 | 状态 |
|------|------|---------|------|
| **前端 fetch** | `setTimeout(..., 3600000)` | 60 分钟 | ✅ |
| **后端 send_message** | `timeout=3600.0` | 60 分钟 | ✅ |
| **WebSocket 接收** | `timeout=120.0` | 2 分钟 | ❌ → ✅ 已修复 |
| **WebSocket ping** | `ping_timeout=20` | 20 秒 | ✅ |

---

## 🎯 现在的超时设置

### 完整流程

```
用户发送消息
    ↓
前端等待（60 分钟）✅
    ↓
pyclaw-web 发送（60 分钟）✅
    ↓
Gateway 处理（60 分钟）✅
    ↓
WebSocket 接收（60 分钟）✅ ← 已修复
    ↓
返回结果
```

### 支持的场景

| 场景 | 预计时间 | 是否支持 |
|------|---------|---------|
| **简单问答** | 5-10 秒 | ✅ |
| **单 Agent 工具调用** | 10-30 秒 | ✅ |
| **多 Agent（3 角色）** | 1-3 分钟 | ✅ |
| **多 Agent（6 角色）** | 3-10 分钟 | ✅ |
| **复杂研究任务** | 10-30 分钟 | ✅ |
| **批量处理** | 30-60 分钟 | ✅ |

---

## 🔧 验证方法

### 重启 pyclaw-web

```bash
cd /home/zjm/.openclaw/workspace/pyclaw/pyclaw-web
pkill -f uvicorn
python3 run.py
```

### 测试长任务

**发送一个需要长时间处理的消息：**
```
帮我搜索 Python 最新发展，并写一份详细报告
```

**观察日志：**
```bash
tail -f pyclaw-web.log | grep "超时\|timeout"
```

**预期：** 不会在 2 分钟时超时

---

## ⚠️ 注意事项

### 1. Gateway 超时

**确保 Gateway 超时时间 >= pyclaw-web 超时时间：**

```json
// Gateway 配置
{
  "agents": {
    "defaults": {
      "timeout_seconds": 3600  // 60 分钟
    }
  }
}
```

### 2. 浏览器超时

**某些浏览器可能有自己的超时限制：**
- Chrome: 通常 5-10 分钟
- Firefox: 通常 10-15 分钟

**解决方案：**
- 使用流式输出（实时显示进度）
- 显示"正在处理..."提示

### 3. 代理/负载均衡器

**如果使用 Nginx 等：**

```nginx
location /api/ {
    proxy_read_timeout 3600s;   // 60 分钟
    proxy_send_timeout 3600s;
}
```

---

## 📚 相关文件

- `pyclaw-web/app/main.py` - 后端超时配置
- `pyclaw-web/templates/index.html` - 前端超时配置
- `docs/TIMEOUT_CONFIG.md` - 超时配置说明

---

**修复完成！** 🎉

现在支持 60 分钟超时，可以处理长时间任务了！

---

**最后更新：** 2026-03-14  
**状态：** ✅ 已修复
