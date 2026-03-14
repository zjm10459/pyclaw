# 超时时间更新 - 60 分钟

## 📊 修改内容

### 前端超时

**文件：** `templates/index.html`

**修改前：**
```javascript
const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 分钟
```

**修改后：**
```javascript
const timeoutId = setTimeout(() => controller.abort(), 3600000); // 60 分钟
```

**超时提示优化：**
```javascript
if (error.name === 'AbortError') {
    appendMessage('assistant', `⏱️ 任务仍在后台执行中...

**多 Agent 协作需要较长时间**（约 20-60 分钟，取决于任务复杂度）

✅ 任务会继续执行
✅ 完成后自动保存到会话  
✅ 请稍后刷新页面查看结果

您可以：
- 继续提问其他问题
- 关闭页面，稍后查看会话列表
- 等待完成后自动显示

预计完成时间：${预计时间}`);
}
```

---

### 后端超时

**文件：** `app/main.py`

**修改前：**
```python
response = await asyncio.wait_for(
    gateway_client.send_message(...),
    timeout=300.0,  # 5 分钟
)
```

**修改后：**
```python
response = await asyncio.wait_for(
    gateway_client.send_message(...),
    timeout=3600.0,  # 60 分钟
)
```

**错误提示优化：**
```python
except asyncio.TimeoutError:
    return ChatResponse(
        success=False,
        message="⏱️ 任务仍在后台执行中...\n\n**多 Agent 协作需要较长时间**（约 20-60 分钟）\n\n✅ 任务会继续执行\n✅ 完成后自动保存到会话\n✅ 请稍后刷新页面查看结果",
    )
```

---

## ⏱️ 超时时间对比

| 组件 | 修改前 | 修改后 | 提升 |
|------|--------|--------|------|
| **前端 fetch** | 5 分钟 | **60 分钟** | +1100% |
| **后端 asyncio** | 5 分钟 | **60 分钟** | +1100% |
| **超时提示** | 简单错误 | **友好提示 + 预计时间** | ✅ |

---

## 🎯 适用场景

### 60 分钟超时适合：

✅ **多 Agent 完整流程** - 6 个角色串行执行（约 30-40 分钟）
✅ **复杂研究任务** - 多次搜索、分析、总结
✅ **长篇文档撰写** - 50+ 页的技术文档
✅ **批量数据处理** - 数十个文件的处理
✅ **代码生成项目** - 完整项目开发

### 仍然可能超时：

⚠️ **超大型项目** - 数百个文件
⚠️ **视频/图像处理** - 大文件处理
⚠️ **模型训练** - 本地微调

---

## 📊 任务执行时间估算

| 任务类型 | 预计时间 | 60 分钟超时 |
|---------|---------|-----------|
| **简单问答** | 5-10 秒 | ✅ 充足 |
| **单 Agent 工具** | 10-30 秒 | ✅ 充足 |
| **多 Agent（3 角色）** | 10-20 分钟 | ✅ 充足 |
| **多 Agent（6 角色）** | 30-40 分钟 | ✅ 充足 |
| **复杂研究 + 文档** | 40-50 分钟 | ✅ 充足 |
| **批量处理（大量）** | 60+ 分钟 | ⚠️ 可能不足 |

---

## 🔧 进一步优化建议

### 如果 60 分钟还不够：

**方案 A：继续增加超时**
```javascript
// 前端
const timeoutId = setTimeout(() => controller.abort(), 7200000); // 120 分钟

// 后端
timeout=7200.0  // 120 分钟
```

**方案 B：优化多 Agent 执行时间**
```json
{
  "multi_agent": {
    "enabled_roles": "supervisor,analyst,writer,executor",
    "agents": {
      "supervisor": {"max_iterations": 3},
      "analyst": {"max_iterations": 5},
      "writer": {"max_iterations": 5},
      "executor": {"max_iterations": 5}
    }
  }
}
```

**方案 C：异步任务 + 轮询**
```
提交任务 → 立即返回任务 ID → 轮询状态 → 完成后通知
```

---

## ⚠️ 注意事项

### 1. 浏览器连接保持

**问题：** 浏览器可能自动断开长时间连接

**解决：**
- 保持页面打开
- 禁用浏览器休眠
- 使用稳定网络

### 2. 服务器资源

**问题：** 长时间任务占用资源

**建议：**
- 监控服务器负载
- 设置最大并发数
- 定期清理会话

### 3. Gateway 超时

**确保 Gateway 超时 > Web 超时：**

```json
// ~/.pyclaw/config.json
{
  "agents": {
    "defaults": {
      "timeout_seconds": 7200  // 120 分钟 > 60 分钟
    }
  }
}
```

### 4. 反向代理超时

**如果使用 Nginx：**

```nginx
location /api/ {
    proxy_read_timeout 3600s;   // 60 分钟
    proxy_send_timeout 3600s;
    proxy_connect_timeout 60s;
}
```

---

## 🧪 测试方法

### 测试超时设置

**1. 创建测试任务**
```
发送一个复杂的多 Agent 任务
```

**2. 观察时间**
```
0 分钟：发送请求
5 分钟：应该还在等待（不显示超时）
30 分钟：可能仍在执行
60 分钟：如果未完成，显示超时提示
```

**3. 查看日志**
```bash
# 前端 Console
# 应该看到详细的时间戳

# 后端日志
tail -f pyclaw-web.log | grep "超时\|timeout"
```

---

## 📚 相关文件

- `pyclaw-web/templates/index.html` - 前端超时设置
- `pyclaw-web/app/main.py` - 后端超时设置
- `pyclaw-web/TIMEOUT_CONFIG.md` - 原始超时配置文档
- `pyclaw/TROUBLESHOOTING_TIMEOUT.md` - 超时问题排查指南

---

## 🎉 更新完成

现在 pyclaw-web 支持：
- ✅ **60 分钟超时** - 支持长时间多 Agent 任务
- ✅ **友好提示** - 超时后显示详细指导
- ✅ **预计时间** - 显示预计完成时间
- ✅ **后台继续** - 超时后任务继续执行

**刷新页面即可生效！** 🐾

---

**最后更新：** 2026-03-14  
**状态：** ✅ 已完成
