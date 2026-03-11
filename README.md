# PyClaw v2.0

OpenClaw 的 Python 实现，基于 LangGraph 的多 Agent 协作系统。

## 核心特性

- ✅ **LangGraph Agent** - 支持多轮工具调用循环
- ✅ **多 Agent 协作** - 主管 + 专家角色分工
- ✅ **RAG 记忆系统** - BM25 + 向量混合检索
- ✅ **Heartbeat 调度器** - 定时任务系统
- ✅ **工作区文件注入** - 人格记忆、USER.md 等自动加载

## 快速启动

```bash
# 安装依赖
pip install langchain langchain-community langgraph sentence-transformers

# 设置环境变量
export DASHSCOPE_API_KEY="your-api-key"

# 启动
python main.py --verbose
```

## 配置

创建 `~/.pyclaw/config.json`:

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
  },
  "rag": {
    "retrieval_method": "hybrid",
    "hybrid_alpha": 0.5,
    "use_mmr": true
  }
}
```

## 项目结构

```
pyclaw/
├── main.py                    # 主入口
├── agents/
│   ├── langgraph_agent.py     # LangGraph Agent
│   └── multi_agent.py         # 多 Agent 协作
├── memory/
│   ├── rag_memory.py          # RAG 记忆系统
│   ├── rag_memory_full.py     # 完整检索版
│   └── advanced_retrieval.py  # 高级检索算法
├── scheduler/
│   └── heartbeat.py           # Heartbeat 调度器
├── gateway/
│   └── server.py              # Gateway 服务器
├── channels/                  # 渠道模块
├── skills/                    # 技能模块
├── tools/                     # 工具模块
└── sessions/                  # 会话管理
```

## 文档

- `QUICKSTART.md` - 快速启动指南
- `MIGRATION_COMPLETE.md` - 迁移报告
- `RAG_MEMORY.md` - RAG 记忆系统
- `RETRIEVAL_COMPARISON.md` - 检索技术对比
- `HEARTBEAT_SCHEDULER.md` - 定时任务系统

## 技术栈

- **LangChain/LangGraph** - Agent 编排
- **sentence-transformers** - 向量嵌入
- **WebSocket** - Gateway 通信
- **Feishu** - 飞书集成

## 版本

- **v2.0** - LangGraph + 多 Agent + RAG
- **v1.0** - 基础 AgentLoop

## License

MIT
