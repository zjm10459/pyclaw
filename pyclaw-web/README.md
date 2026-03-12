# PyClaw Web - FastAPI 聊天监控系统

基于 FastAPI 构建的 Web 聊天界面，用于监控和使用 PyClaw 服务。

## 🚀 快速开始

### 1. 安装依赖

```bash
cd pyclaw-web

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
# PyClaw Web 配置
PYCLAW_WEB_HOST=127.0.0.1
PYCLAW_WEB_PORT=18800

# PyClaw Gateway 地址
PYCLAW_GATEWAY_URL=ws://127.0.0.1:18790
PYCLAW_GATEWAY_TOKEN=
```

### 3. 启动服务

```bash
# 方式 1：使用启动脚本
./start.sh

# 方式 2：直接运行
python app/main.py

# 方式 3：使用 uvicorn
uvicorn app.main:app --host 127.0.0.1 --port 18800
```

### 4. 访问 Web 界面

打开浏览器访问：**http://127.0.0.1:18800**

---

## 📋 功能特性

### ✅ 核心功能

- **Web 聊天界面** - 现代化的聊天 UI
- **实时通信** - WebSocket 实时消息推送
- **会话管理** - 创建、切换、删除会话
- **历史记录** - 查看聊天历史
- **多 Agent 模式** - 支持单 Agent 和多 Agent 协作切换

### 🎨 界面特点

- 响应式设计
- 渐变配色方案
- 流畅动画效果
- 消息时间戳
- 输入框自动调整

---

## 🔌 API 接口

### RESTful API

#### 获取系统状态
```http
GET /api/status
```

#### 列出所有会话
```http
GET /api/sessions
```

#### 获取会话详情
```http
GET /api/sessions/{session_id}
```

#### 获取会话历史
```http
GET /api/sessions/{session_id}/history?limit=50
```

#### 发送聊天消息
```http
POST /api/chat
Content-Type: application/json

{
    "session_id": "session_123",
    "message": "你好",
    "mode": "single"
}
```

#### 删除会话
```http
DELETE /api/sessions/{session_id}
```

### WebSocket

#### 实时通信
```
WS /ws/{session_id}
```

**客户端发送:**
```json
{
    "message": "你好",
    "mode": "single"
}
```

**服务器响应:**
```json
{
    "type": "response",
    "data": {
        "success": true,
        "output": "你好！有什么可以帮你的吗？",
        "session_id": "session_123"
    }
}
```

---

## 🏗️ 项目结构

```
pyclaw-web/
├── app/
│   └── main.py          # FastAPI 主应用
├── templates/
│   └── index.html       # Web 界面模板
├── static/              # 静态文件（可选）
├── requirements.txt     # Python 依赖
├── start.sh            # 启动脚本
├── .env.example        # 环境变量示例
└── README.md           # 本文档
```

---

## ⚙️ 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `PYCLAW_WEB_HOST` | Web 服务监听地址 | `127.0.0.1` |
| `PYCLAW_WEB_PORT` | Web 服务端口 | `18800` |
| `PYCLAW_GATEWAY_URL` | PyClaw Gateway 地址 | `ws://127.0.0.1:18790` |
| `PYCLAW_GATEWAY_TOKEN` | Gateway 认证令牌 | - |

### 前置要求

1. **PyClaw Gateway 必须运行**
   ```bash
   cd ../pyclaw
   python main.py --port 18790
   ```

2. **确保端口未被占用**
   - Web 端口：18800
   - Gateway 端口：18790

---

## 💡 使用示例

### 1. 创建会话

点击 "+ 新建会话" 按钮创建新会话。

### 2. 切换模式

在右上角选择：
- **单 Agent** - 标准 AI 助手
- **多 Agent 协作** - 多专家协作处理复杂任务

### 3. 发送消息

在输入框输入消息，按 Enter 发送（Shift+Enter 换行）。

### 4. 查看历史

点击左侧会话列表查看历史聊天记录。

---

## 🔧 开发

### 热重载开发

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 18800
```

### 添加新功能

1. 在 `app/main.py` 添加 API 路由
2. 在 `templates/index.html` 更新前端逻辑
3. 测试功能

---

## 📝 注意事项

1. **Gateway 依赖** - Web 服务需要 PyClaw Gateway 运行才能正常工作
2. **会话隔离** - 每个会话独立存储，互不干扰
3. **WebSocket 重连** - 断开后自动尝试重连（3 秒间隔）
4. **消息限制** - 单次请求超时时间为 120 秒

---

## 🐛 故障排查

### Gateway 未连接

```bash
# 检查 Gateway 是否运行
curl http://127.0.0.1:18790

# 查看 Gateway 日志
tail -f ~/.pyclaw/logs/gateway.log
```

### 端口被占用

```bash
# 查看端口占用
lsof -i :18800

# 修改端口
export PYCLAW_WEB_PORT=18801
```

### WebSocket 连接失败

检查浏览器控制台错误，确保：
- Gateway 服务正常运行
- 防火墙未阻止 WebSocket
- 浏览器支持 WebSocket

---

## 📄 许可证

MIT License

---

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/)
- [PyClaw](https://github.com/zjm10459/pyclaw)
