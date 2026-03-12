# PyClaw 配置指南

本文档说明 PyClaw 项目的所有配置项及其位置。

## 📁 配置文件位置

### 推荐位置（按优先级）

1. **`~/.pyclaw/config.json`** - 用户主目录（推荐 ✅）
2. **`./config.json`** - 项目根目录
3. **`--config /path/to/config.json`** - 命令行指定

### 环境变量文件

- **`~/.pyclaw/.env`** - 用户主目录（推荐 ✅）
- **`./.env`** - 项目根目录

---

## 🔑 配置文件说明

### 1. config.json - 主配置文件

**位置：** `~/.pyclaw/config.json` 或 `./config.json`

**包含所有配置项：**

```json
{
  "workspace": "~/.pyclaw/workspace",
  
  "agents": {
    "defaults": {
      "model": "qwen3.5-plus",
      "provider": "bailian",
      "temperature": 0.7,
      "max_tokens": 4096,
      "max_iterations": 10,
      "system_prompt": "你是一个有帮助的 AI 助手，使用中文回复。"
    }
  },
  
  "providers": {
    "bailian": {
      "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
      "api_key": "${DASHSCOPE_API_KEY}"
    },
    "openai": {
      "base_url": "https://api.openai.com/v1",
      "api_key": "${OPENAI_API_KEY}"
    },
    "anthropic": {
      "api_key": "${ANTHROPIC_API_KEY}"
    }
  },
  
  "memory": {
    "path": "~/.pyclaw/memory"
  },
  
  "sessions": {
    "isolation": "per-channel-peer"
  },
  
  "heartbeat": {
    "enable_email": false,
    "enable_calendar": false,
    "enable_weather": false,
    "default_interval_minutes": 30
  },
  
  "rag": {
    "enable_vector_search": true,
    "chunk_size": 500,
    "chunk_overlap": 50,
    "top_k": 5,
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "vector_store": "memory",
    "retrieval_method": "hybrid",
    "hybrid_alpha": 0.5,
    "use_mmr": true,
    "mmr_lambda": 0.5,
    "use_rerank": false,
    "rerank_model": "cross-encoder/ms-marco-MiniLM-L-6-v2"
  },
  
  "multi_agent": {
    "enabled_roles": "supervisor,researcher,coder,writer,analyst,executor",
    "agents": {
      "supervisor": {
        "model": "qwen3.5-plus",
        "provider": "bailian",
        "temperature": 0.7,
        "max_tokens": 4096,
        "max_iterations": 5
      },
      "researcher": {
        "model": "qwen3.5-plus",
        "provider": "bailian",
        "temperature": 0.5,
        "max_tokens": 4096
      },
      "coder": {
        "model": "qwen2.5-coder-32b",
        "provider": "bailian",
        "temperature": 0.3,
        "max_tokens": 4096
      },
      "writer": {
        "model": "qwen3.5-plus",
        "provider": "bailian",
        "temperature": 0.8,
        "max_tokens": 4096
      },
      "analyst": {
        "model": "qwen3.5-plus",
        "provider": "bailian",
        "temperature": 0.5,
        "max_tokens": 4096
      },
      "executor": {
        "model": "qwen3-turbo",
        "provider": "bailian",
        "temperature": 0.7,
        "max_tokens": 2048
      }
    }
  },
  
  "channels": {
    "feishu": {
      "enabled": false,
      "app_id": "",
      "app_secret": "",
      "verification_token": "",
      "encrypt_key": "",
      "host": "0.0.0.0",
      "port": 18791
    }
  },
  
  "server": {
    "host": "127.0.0.1",
    "port": 18790,
    "auth_token": ""
  }
}
```

### 2. .env - 环境变量文件

**位置：** `~/.pyclaw/.env` 或 `./.env`

**包含敏感信息（API Key 等）：**

```bash
# 阿里云百炼（通义千问）- 推荐
DASHSCOPE_API_KEY=sk-your-dashscope-api-key-here

# OpenAI（可选）
OPENAI_API_KEY=sk-your-openai-api-key-here

# Anthropic（可选）
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here

# 飞书渠道配置（可选）
FEISHU_APP_ID=cli_xxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxx
FEISHU_VERIFICATION_TOKEN=your-verification-token

# Gateway 配置
PYCLAW_GATEWAY_PORT=18789
PYCLAW_GATEWAY_HOST=0.0.0.0

# 日志级别
PYCLAW_LOG_LEVEL=INFO
```

---

## 📋 配置项详解

### 核心配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `workspace` | 工作区路径 | `~/.pyclaw/workspace` |
| `memory.path` | 记忆存储路径 | `~/.pyclaw/memory` |

### Agent 配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `agents.defaults.model` | 默认模型 | `qwen3.5-plus` |
| `agents.defaults.provider` | 默认 Provider | `bailian` |
| `agents.defaults.temperature` | 温度参数 | `0.7` |
| `agents.defaults.max_tokens` | 最大输出 token | `4096` |
| `agents.defaults.max_iterations` | 最大迭代次数 | `10` |
| `agents.defaults.system_prompt` | 系统提示词 | - |

### Provider 配置

| Provider | base_url | 环境变量 |
|----------|----------|----------|
| bailian | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `DASHSCOPE_API_KEY` |
| openai | `https://api.openai.com/v1` | `OPENAI_API_KEY` |
| anthropic | - | `ANTHROPIC_API_KEY` |

### 多 Agent 配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `multi_agent.enabled_roles` | 启用的 Agent 角色 | 所有角色 |
| `multi_agent.agents.*.model` | 各 Agent 的模型 | 见 config.example.json |
| `multi_agent.agents.*.temperature` | 各 Agent 的温度 | 见 config.example.json |

**可用 Agent 角色：**
- `supervisor` - 主管（任务分解协调）
- `researcher` - 研究员（信息收集）
- `coder` - 程序员（代码编写）
- `writer` - 作家（文案创作）
- `analyst` - 分析师（数据分析）
- `executor` - 执行者（任务执行）

### RAG 配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `rag.enable_vector_search` | 启用向量搜索 | `true` |
| `rag.chunk_size` | 分块大小 | `500` |
| `rag.chunk_overlap` | 分块重叠 | `50` |
| `rag.top_k` | 检索结果数 | `5` |
| `rag.embedding_model` | 嵌入模型 | `sentence-transformers/all-MiniLM-L6-v2` |
| `rag.retrieval_method` | 检索方法 | `hybrid` |

### Heartbeat 配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `heartbeat.enable_email` | 启用邮件检查 | `false` |
| `heartbeat.enable_calendar` | 启用日历检查 | `false` |
| `heartbeat.enable_weather` | 启用天气检查 | `false` |
| `heartbeat.default_interval_minutes` | 检查间隔（分钟） | `30` |

### 渠道配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `channels.feishu.enabled` | 启用飞书 | `false` |
| `channels.feishu.app_id` | 飞书 App ID | - |
| `channels.feishu.app_secret` | 飞书 App Secret | - |
| `channels.feishu.verification_token` | 飞书验证 Token | - |
| `channels.feishu.port` | 飞书服务端口 | `18791` |

### 服务器配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `server.host` | 监听地址 | `127.0.0.1` |
| `server.port` | 监听端口 | `18790` |
| `server.auth_token` | 认证令牌 | - |

---

## 🚀 快速开始

### 步骤 1：创建配置目录

```bash
mkdir -p ~/.pyclaw
```

### 步骤 2：复制示例配置

```bash
# 复制主配置
cp config.example.json ~/.pyclaw/config.json

# 复制环境变量示例
cp .env.example ~/.pyclaw/.env
```

### 步骤 3：编辑配置

```bash
# 编辑主配置
vim ~/.pyclaw/config.json

# 编辑环境变量（填入 API Key）
vim ~/.pyclaw/.env
```

### 步骤 4：启动服务

```bash
# 使用默认配置启动
python main.py

# 指定配置文件启动
python main.py --config /path/to/config.json

# 启用多 Agent 模式
python main.py --multi-agent
```

---

## 💡 最佳实践

### ✅ 推荐做法

1. **使用 `~/.pyclaw/` 目录** - 配置集中管理，与代码分离
2. **敏感信息放在 `.env`** - API Key 等不要放入 `config.json`
3. **使用 `${ENV_VAR}` 语法** - 在 `config.json` 中引用环境变量
4. **按需启用 Agent** - 只启用需要的 Agent 角色，节省资源

### ❌ 避免做法

1. **不要硬编码 API Key** - 始终使用环境变量
2. **不要提交 `.env` 到 Git** - 已添加到 `.gitignore`
3. **不要在生产环境使用默认配置** - 修改默认密码和令牌

---

## 🔗 相关文件

- `config.example.json` - 配置示例（完整注释版）
- `.env.example` - 环境变量示例
- `README.md` - 项目说明
- `docs/` - 详细文档

---

## ❓ 常见问题

### Q: 配置文件放在哪里？
A: 推荐放在 `~/.pyclaw/config.json`，也可以放在项目根目录或通过 `--config` 指定。

### Q: 为什么需要两个配置文件？
A: `config.json` 存放普通配置，`.env` 存放敏感信息（API Key）。这样更安全，也便于分享配置。

### Q: 如何自定义 Agent 配置？
A: 在 `config.json` 的 `multi_agent.agents` 中配置每个 Agent 的模型和参数。

### Q: 配置修改后需要重启吗？
A: 是的，配置在服务启动时加载，修改后需要重启服务。

---

**最后更新：** 2026-03-12
