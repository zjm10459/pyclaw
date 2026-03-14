# 多 Agent 超时问题排查指南

## 🐛 常见超时原因

### 1. API Key 无效或过期 ⭐⭐⭐⭐⭐

**症状：** 请求立即超时或返回认证错误

**检查方法：**
```bash
# 测试 API Key 是否有效
curl -X POST https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions \
  -H "Authorization: Bearer sk-sp-1449eadf40684bd087a87a8d2532eb1a" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3.5-plus","messages":[{"role":"user","content":"你好"}]}'
```

**解决方案：**
- 检查配置文件中的 API Key 是否正确
- 登录阿里云百炼控制台验证 API Key 状态
- 确保账户有足够余额

---

### 2. 网络连接问题 ⭐⭐⭐⭐

**症状：** 请求超时，无任何响应

**检查方法：**
```bash
# 测试网络连接
ping dashscope.aliyuncs.com

# 测试 API 端点
curl -I https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
```

**解决方案：**
- 检查防火墙设置
- 检查代理配置
- 尝试切换网络环境

---

### 3. 模型名称错误 ⭐⭐⭐⭐

**症状：** 返回 404 或模型不存在错误

**检查方法：**
```bash
# 查看配置文件中的模型名称
cat config.high-performance.json | grep model
```

**正确的模型名称（阿里云百炼）：**
```json
{
  "supervisor": "qwen-max",  // ✅ 正确
  "researcher": "kimi-k2.5",  // ✅ 正确
  "coder": "qwen-coder-plus",  // ✅ 正确
  "writer": "minimax-m2.5",  // ✅ 正确
  "analyst": "glm-5",  // ✅ 正确
  "executor": "qwen-plus"  // ✅ 正确
}
```

**错误的模型名称：**
```json
{
  "supervisor": "qwen3-max-2026-01-23",  // ❌ 可能不存在
  "coder": "qwen3-coder-plus"  // ❌ 可能不存在
}
```

**解决方案：**
- 使用阿里云百炼控制台确认模型名称
- 参考官方文档：https://help.aliyun.com/zh/dashscope/

---

### 4. 超时时间设置过短 ⭐⭐⭐

**症状：** 请求在固定时间后超时（如 30 秒）

**解决方案：** 增加超时时间

修改 `config.high-performance.json`：
```json
{
  "agents": {
    "defaults": {
      "request_timeout": 120,  // 增加到 120 秒
      "max_iterations": 10
    }
  }
}
```

---

### 5. 多 Agent 嵌套调用问题 ⭐⭐⭐

**症状：** 单 Agent 正常，多 Agent 超时

**原因：** 多 Agent 系统中，每个 Agent 都会调用 API，总时间累加

**解决方案：**

**方案 A：减少 Agent 数量**
```json
{
  "multi_agent": {
    "enabled_roles": "supervisor,coder,writer"  // 只启用核心角色
  }
}
```

**方案 B：降低 max_iterations**
```json
{
  "multi_agent": {
    "agents": {
      "supervisor": {
        "max_iterations": 3  // 从 5 降低到 3
      },
      "coder": {
        "max_iterations": 5  // 从 10 降低到 5
      }
    }
  }
}
```

**方案 C：使用更快的模型**
```json
{
  "multi_agent": {
    "agents": {
      "supervisor": {
        "model": "qwen-plus"  // 使用更快的模型
      },
      "executor": {
        "model": "qwen-turbo"  // 使用最快的模型
      }
    }
  }
}
```

---

### 6. 并发请求限制 ⭐⭐

**症状：** 第一个请求成功，后续请求超时

**原因：** API 有并发限制或速率限制

**解决方案：**
```json
{
  "multi_agent": {
    "max_concurrent_agents": 2  // 限制并发 Agent 数量
  }
}
```

---

## 🔧 快速修复方案

### 方案 1：使用简化配置（推荐测试用）

创建 `config.multi-agent-simple.json`：

```json
{
  "workspace": "~/.pyclaw/workspace",
  
  "agents": {
    "defaults": {
      "model": "qwen-plus",
      "provider": "bailian",
      "temperature": 0.7,
      "max_tokens": 2048,
      "max_iterations": 5,
      "request_timeout": 120
    }
  },
  
  "providers": {
    "bailian": {
      "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
      "api_key": "你的 API Key"
    }
  },
  
  "multi_agent": {
    "enabled_roles": "supervisor,writer,executor",
    "agents": {
      "supervisor": {
        "model": "qwen-plus",
        "temperature": 0.7,
        "max_iterations": 3
      },
      "writer": {
        "model": "qwen-plus",
        "temperature": 0.8,
        "max_iterations": 5
      },
      "executor": {
        "model": "qwen-turbo",
        "temperature": 0.7,
        "max_iterations": 5
      }
    }
  }
}
```

**特点：**
- ✅ 只使用 3 个 Agent（减少总时间）
- ✅ 使用更快的模型
- ✅ 降低迭代次数
- ✅ 增加超时时间

---

### 方案 2：分步测试

**步骤 1：测试单 Agent**
```bash
# 不使用多 Agent，测试基础功能
python main.py
# 发送简单消息测试
```

**步骤 2：测试双 Agent**
```json
{
  "multi_agent": {
    "enabled_roles": "supervisor,executor"
  }
}
```

**步骤 3：测试完整多 Agent**
```json
{
  "multi_agent": {
    "enabled_roles": "supervisor,researcher,coder,writer,analyst,executor"
  }
}
```

---

### 方案 3：增加日志详细度

修改配置，添加详细日志：

```json
{
  "logging": {
    "level": "DEBUG",
    "file": "pyclaw.log"
  }
}
```

**启动时查看详细日志：**
```bash
python main.py --multi-agent --verbose 2>&1 | tee pyclaw.log
```

**分析日志：**
```bash
# 查看超时相关日志
grep -i "timeout\|超时\|error" pyclaw.log

# 查看 API 调用时间
grep "API call\|request" pyclaw.log
```

---

## 📊 超时时间估算

### 单 Agent 响应时间

| 模型 | 平均响应时间 | 95% 响应时间 |
|------|------------|------------|
| qwen-turbo | 1-3 秒 | 5 秒 |
| qwen-plus | 3-5 秒 | 10 秒 |
| qwen-max | 5-10 秒 | 20 秒 |
| kimi-k2.5 | 5-10 秒 | 20 秒 |
| glm-5 | 5-10 秒 | 20 秒 |

### 多 Agent 总时间估算

**示例：6 角色完整流程**

```
主管分析 (10 秒)
  ↓
研究员执行 (15 秒)
  ↓
程序员执行 (15 秒)
  ↓
作家执行 (10 秒)
  ↓
分析师执行 (10 秒)
  ↓
主管汇总 (10 秒)
  ↓
总计：70 秒 ≈ 1 分 10 秒
```

**建议超时设置：**
- 单 Agent：30 秒
- 双 Agent：60 秒
- 完整多 Agent：120 秒

---

## ⚡ 性能优化建议

### 1. 选择合适的模型组合

**快速版（响应优先）：**
```json
{
  "supervisor": "qwen-plus",
  "researcher": "qwen-plus",
  "coder": "qwen-coder-turbo",
  "writer": "qwen-plus",
  "analyst": "qwen-plus",
  "executor": "qwen-turbo"
}
```

**均衡版（性能 + 速度）：**
```json
{
  "supervisor": "qwen-max",
  "researcher": "qwen-plus",
  "coder": "qwen-coder-plus",
  "writer": "qwen-plus",
  "analyst": "qwen-plus",
  "executor": "qwen-plus"
}
```

**高配版（质量优先）：**
```json
{
  "supervisor": "qwen-max",
  "researcher": "kimi-k2.5",
  "coder": "qwen-coder-plus",
  "writer": "minimax-m2.5",
  "analyst": "glm-5",
  "executor": "qwen-plus"
}
```

### 2. 减少不必要的迭代

```json
{
  "agents": {
    "defaults": {
      "max_iterations": 5  // 从 10 降低到 5
    }
  }
}
```

### 3. 使用流式输出

```bash
# 启用流式输出，可以看到实时进度
python main.py --multi-agent --stream
```

---

## 📞 获取帮助

### 收集以下信息

1. **配置文件**
```bash
cat config.high-performance.json | grep -v "api_key"
```

2. **错误日志**
```bash
tail -100 pyclaw.log
```

3. **网络测试**
```bash
curl -I https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
```

4. **Python 版本**
```bash
python3 --version
```

---

## 🔗 参考资源

- [阿里云百炼文档](https://help.aliyun.com/zh/dashscope/)
- [API 超时设置](https://help.aliyun.com/zh/dashscope/developer-reference/timeout)
- [错误码说明](https://help.aliyun.com/zh/dashscope/developer-reference/error-code)

---

**最后更新：** 2026-03-14  
**状态：** 故障排查指南
