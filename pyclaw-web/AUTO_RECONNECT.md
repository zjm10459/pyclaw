# ✅ 断连重连功能实现

## 📊 功能说明

pyclaw-web 现在支持 **WebSocket 断连自动重连**，提高连接稳定性和用户体验。

---

## 🔧 实现内容

### 1. 连接状态管理

**新增属性：**
```python
class PyClawGatewayClient:
    def __init__(self):
        self.connected = False              # 连接状态
        self.reconnect_attempts = 0         # 重连尝试次数
        self.max_reconnect_attempts = 5     # 最大重连次数
        self.reconnect_delay = 5            # 重连延迟（秒）
```

---

### 2. 重连机制

**重连方法：**
```python
async def reconnect(self):
    """断连重连（带重试机制）"""
    if self.reconnect_attempts >= self.max_reconnect_attempts:
        logger.error("已达到最大重试次数")
        return False
    
    self.reconnect_attempts += 1
    logger.info(f"尝试重连 ({self.reconnect_attempts}/{self.max_reconnect_attempts})...")
    
    # 关闭旧连接
    if self.ws:
        await self.ws.close()
    
    # 延迟后重连
    await asyncio.sleep(self.reconnect_delay)
    
    # 尝试连接
    await self.connect()
    
    return True
```

---

### 3. 连接确保

**确保连接方法：**
```python
async def ensure_connected(self):
    """确保连接（如果断开则重连）"""
    if not self.connected:
        return await self.reconnect()
    
    # 检查 WebSocket 状态
    if self.ws.state != State.OPEN:
        self.connected = False
        return await self.reconnect()
    
    return True
```

---

### 4. 发送消息时自动重连

**修改 send_message：**
```python
async def send_message(self, session_id, message, mode):
    # 确保连接正常
    connected = await self.ensure_connected()
    if not connected:
        return {"success": False, "error": "无法连接到 Gateway"}
    
    try:
        await self.ws.send(request)
    except Exception as e:
        # 发送失败时尝试重连
        connected = await self.reconnect()
        if connected:
            await self.ws.send(request)  # 重连后重试
```

---

## 📊 重连策略

### 重连参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| **max_reconnect_attempts** | 5 | 最大重连次数 |
| **reconnect_delay** | 5 秒 | 每次重连间隔 |
| **总重试时间** | 25 秒 | 5 次 × 5 秒 |

### 重连流程

```
连接断开
    ↓
检测到断开（发送消息时）
    ↓
尝试重连 (1/5)
    ↓ 失败
等待 5 秒
    ↓
尝试重连 (2/5)
    ↓ 失败
等待 5 秒
    ↓
...
    ↓
尝试重连 (5/5)
    ↓ 失败
返回错误："无法连接到 Gateway"
```

---

## 🎯 使用场景

### 场景 1：网络波动

```
用户发送消息
    ↓
检测到连接断开
    ↓
自动重连（用户无感知）
    ↓
消息发送成功 ✅
```

### 场景 2：Gateway 重启

```
Gateway 重启
    ↓
pyclaw-web 检测到断开
    ↓
等待 Gateway 就绪
    ↓
自动重连成功 ✅
    ↓
继续正常工作
```

### 场景 3：长时间空闲

```
用户长时间未操作
    ↓
WebSocket 超时断开
    ↓
用户再次发送消息
    ↓
自动重连 ✅
    ↓
消息正常发送
```

---

## 📝 日志示例

### 正常重连

```
INFO: 检测到连接断开，尝试重连...
INFO: 尝试重连 Gateway (1/5)...
INFO: WebSocket 已连接：ws://127.0.0.1:18790
INFO: ✓ Gateway 连接成功
INFO: ✓ 重连成功
```

### 重连失败

```
ERROR: 连接 Gateway 失败：Connection refused
INFO: 尝试重连 Gateway (1/5)...
ERROR: 重连失败：Connection refused
INFO: 尝试重连 Gateway (2/5)...
ERROR: 重连失败：Connection refused
...
ERROR: 重连失败：已达到最大重试次数 (5)
ERROR: 无法连接到 Gateway，请稍后重试
```

---

## ⚙️ 配置选项

### 修改重连参数

编辑 `app/main.py`：

```python
class PyClawGatewayClient:
    def __init__(self):
        self.max_reconnect_attempts = 10  # 增加重连次数
        self.reconnect_delay = 3          # 缩短重连间隔
```

### 禁用重连

```python
self.max_reconnect_attempts = 0  # 禁用重连
```

---

## 🔍 测试方法

### 测试 1：手动断开连接

```bash
# 1. 启动 pyclaw-web
cd /home/zjm/.openclaw/workspace/pyclaw/pyclaw-web
python3 run.py

# 2. 发送一条消息（正常）
# 3. 重启 Gateway
pkill -f "python.*main.py"
python3 /home/zjm/.openclaw/workspace/pyclaw/main.py

# 4. 再次发送消息（应该自动重连）
```

### 测试 2：查看日志

```bash
tail -f /home/zjm/.openclaw/workspace/pyclaw/pyclaw-web/pyclaw-web.log | grep "重连\|连接"
```

---

## ✅ 优势

### 重连前

❌ 连接断开后需要手动重启
❌ 用户看到错误提示
❌ 需要刷新页面

### 重连后

✅ 自动检测断开
✅ 自动重连（用户无感知）
✅ 失败后有友好提示
✅ 提高系统稳定性

---

## ⚠️ 注意事项

1. **重连次数** - 默认 5 次，可根据网络环境调整
2. **重连延迟** - 默认 5 秒，避免频繁重连
3. **错误提示** - 重连失败后显示友好提示
4. **日志记录** - 记录所有重连尝试，便于排查

---

## 📚 相关文件

- `pyclaw-web/app/main.py` - 主程序（已修改）
- `pyclaw-web/AUTO_RECONNECT.md` - 本文档
- `pyclaw-web/TIMEOUT_CONFIG.md` - 超时配置

---

**实现完成！** 🎉

现在 pyclaw-web 支持：
- ✅ 自动检测连接断开
- ✅ 自动重连（最多 5 次）
- ✅ 发送失败自动重试
- ✅ 友好错误提示

重启 pyclaw-web 后生效！🐾
