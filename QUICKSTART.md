# PyClaw 快速启动指南

## 1  分钟快速启动

### 步骤 1: 安装依赖

```bash
cd /home/zjm/.openclaw/workspace/pyclaw
pip install langchain langchain-community langgraph
```

### 步骤 2: 配置环境变量

```bash
export DASHSCOPE_API_KEY="your-api-key"
```

### 步骤 3: 启动服务器

```bash
python main.py
```

### 步骤 4: 测试连接

```bash
# 使用 wscat 或其他 WebSocket 客户端
wscat -c ws://127.0.0.1:18790

# 发送测试消息
{
  "method": "agent",
  "params": {
    "sessionKey": "test:001",
    "input": "你好"
  }
}
```

---

## 配置说明

### 配置文件位置

`~/.pyclaw/config.json`

### 最小配置

```json
{
  "agents": {
    "defaults": {
      "model": "qwen3.5-plus",
      "provider": "bailian",
      "system_prompt": "你是一个有帮助的 AI 助手。"
    }
  },
  "providers": {
    "bailian": {
      "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
      "api_key": "${DASHSCOPE_API_KEY}"
    }
  }
}
```

---

## 启动选项

### 基本启动

```bash
python main.py                    # 默认配置
python main.py --port 18790       # 指定端口
python main.py --token abc123     # 认证令牌
python main.py --verbose          # 详细模式
```

### Agent 模式

```bash
python main.py --agent-mode langgraph   # LangGraph Agent (默认)
python main.py --agent-mode multi       # 多 Agent 协作
python main.py --agent-mode simple      # 旧版 AgentLoop
```

### 多 Agent 协作

```bash
python main.py --multi-agent            # 启用多 Agent
python main.py --multi-agent --verbose  # 详细模式
```

---

## 测试

### 运行测试套件

```bash
python test_langgraph_agent.py
```

### 测试 LangGraph Agent

```bash
python agents/langgraph_agent.py
```

### 测试多 Agent 协作

```bash
python agents/multi_agent.py
```

---

## 工作区文件

启动时会自动创建以下文件（如果不存在）：

- `~/.pyclaw/workspace/人格记忆.md` - AI 身份
- `~/.pyclaw/workspace/长期记忆.md` - 长期记忆
- `~/.pyclaw/workspace/AGENT.md` - 工作区说明
- `~/.pyclaw/workspace/USER.md` - 用户信息
- `~/.pyclaw/workspace/TOOLS.md` - 工具笔记
- `~/.pyclaw/workspace/IDENTITY.md` - 身份元数据
- `~/.pyclaw/workspace/memory/YYYY-MM-DD.md` - 每日记忆

---

## 常见问题

### Q: LLM 初始化失败

**A:** 检查以下几点：
1. 确认 `DASHSCOPE_API_KEY` 环境变量已设置
2. 检查网络连接
3. 确认 API Key 有效

### Q: 端口被占用

**A:** 使用其他端口：
```bash
python main.py --port 18791
```

### Q: 多 Agent 无响应

**A:** 可能是某个 Agent 卡住，检查日志：
```bash
python main.py --verbose
```

---

## 下一步

- 阅读 [MIGRATION_COMPLETE.md](MIGRATION_COMPLETE.md) 了解完整迁移信息
- 阅读 [LANGGRAPH_AGENT_DESIGN.md](LANGGRAPH_AGENT_DESIGN.md) 了解架构设计
- 修改 `~/.pyclaw/config.json` 自定义配置

---

_祝使用愉快！🐾_
