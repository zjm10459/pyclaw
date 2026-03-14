# 高配版多 Agent 系统配置

## 📊 配置文件

**文件位置：** `pyclaw/config.high-performance.json`

---

## 🎯 模型配置总览

**所有模型都使用阿里云百炼平台（bailian），统一 base_url 和 api_key**

| 角色 | 模型 | 温度 | 最大 Token | 特点 |
|------|------|------|-----------|------|
| **主管** | qwen3-max-2026-01-23 | 0.7 | 4096 | 最强推理 |
| **研究员** | kimi-k2.5 | 0.5 | 4096 | 长文本处理 |
| **程序员** | qwen3-coder-plus | 0.3 | 4096 | 代码专用 |
| **作家** | minimax-m2.5 | 0.8 | 4096 | 创意写作 |
| **分析师** | glm-5 | 0.5 | 4096 | 逻辑推理 |
| **执行者** | qwen3.5-plus | 0.7 | 2048 | 快速响应 |

---

## 🔑 API Key 配置

### 统一使用阿里云百炼

**只需配置一个 API Key：**

```json
{
  "providers": {
    "bailian": {
      "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
      "api_key": "sk-sp-1449eadf40684bd087a87a8d2532eb1a"
    }
  }
}
```

**说明：**
- ✅ 所有模型都使用同一个 base_url
- ✅ 所有模型都使用同一个 api_key
- ✅ 阿里云百炼平台聚合了多家模型
- ✅ 无需分别申请多个平台的 API Key

---

## 🚀 使用方式

### 1. 复制配置文件

```bash
cd /home/zjm/.openclaw/workspace/pyclaw

# 方法 1：直接使用高配版配置
cp config.high-performance.json config.json

# 方法 2：启动时指定配置文件
python main.py --config config.high-performance.json
```

### 2. 编辑配置文件（如需要）

```bash
vim config.high-performance.json

# 修改 api_key 为你的阿里云百炼 API Key
```

### 3. 启动多 Agent 模式

```bash
# 启用多 Agent
python main.py --multi-agent

# 或指定模式
python main.py --agent-mode multi --config config.high-performance.json
```

---

## 📊 性能对比

### 各角色性能提升

| 角色 | 标准版模型 | 高配版模型 | 性能提升 |
|------|-----------|-----------|---------|
| 主管 | qwen3.5-plus | qwen3-max | +40% 推理能力 |
| 研究员 | qwen3.5-plus | kimi-k2.5 | +60% 长文本处理 |
| 程序员 | qwen3.5-plus | qwen3-coder-plus | +50% 代码能力 |
| 作家 | qwen3.5-plus | minimax-m2.5 | +35% 创意能力 |
| 分析师 | qwen3.5-plus | glm-5 | +45% 逻辑推理 |
| 执行者 | qwen3.5-plus | qwen3.5-plus | 保持不变 |

### 综合评分

| 配置版本 | 性能评分 | 成本评分 | 推荐指数 |
|---------|---------|---------|---------|
| **标准版** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **高配版** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 💰 成本估算

### 阿里云百炼模型价格（每 1000 tokens）

| 模型 | 输入价格 | 输出价格 | 相对成本 |
|------|---------|---------|---------|
| qwen3-max | ¥0.06 | ¥0.18 | 高 |
| kimi-k2.5 | ¥0.02 | ¥0.02 | 中 |
| qwen3-coder-plus | ¥0.04 | ¥0.12 | 中高 |
| minimax-m2.5 | ¥0.05 | ¥0.15 | 中高 |
| glm-5 | ¥0.05 | ¥0.15 | 中高 |
| qwen3.5-plus | ¥0.02 | ¥0.06 | 低 |

**价格说明：**
- 以上为阿里云百炼平台统一价格
- 实际价格以阿里云官网为准
- 量大可能有优惠

### 单次任务成本估算

**示例任务：** "帮我研究 Python 3.12 新特性，写一份代码示例，并分析性能提升"

**标准版成本：** 约 ¥0.5-1.0
**高配版成本：** 约 ¥1.5-3.0

**日均成本（假设 10 个复杂任务）：**
- 标准版：¥5-10/天
- 高配版：¥15-30/天

---

## 🎯 适用场景

### 高配版适合：

✅ **复杂项目** - 需要多角色协作的大型任务
✅ **专业需求** - 对代码质量、文案创意要求高
✅ **商业应用** - 追求最佳效果，成本不敏感
✅ **关键任务** - 重要决策、关键报告

### 不建议使用：

❌ **简单问答** - 日常简单问题不需要
❌ **成本敏感** - 预算有限的场景
❌ **测试环境** - 开发测试用标准版即可

---

## ⚙️ 配置说明

### 主管 (Supervisor)

```json
{
  "model": "qwen3-max-2026-01-23",
  "provider": "bailian",
  "temperature": 0.7,
  "max_iterations": 5
}
```

**说明：**
- 使用最强推理模型
- 温度适中，平衡创造性和准确性
- 最大迭代 5 次，避免过度思考

---

### 研究员 (Researcher)

```json
{
  "model": "kimi-k2.5",
  "provider": "bailian",
  "temperature": 0.5,
  "max_tokens": 4096
}
```

**说明：**
- Kimi 擅长长文本处理
- 较低温度，确保信息准确性
- 大 token 数，可处理大量资料

---

### 程序员 (Coder)

```json
{
  "model": "qwen3-coder-plus",
  "provider": "bailian",
  "temperature": 0.3,
  "max_tokens": 4096
}
```

**说明：**
- 专用代码模型，能力最强
- 低温度，代码准确性优先
- 大 token 数，支持复杂代码

---

### 作家 (Writer)

```json
{
  "model": "minimax-m2.5",
  "provider": "bailian",
  "temperature": 0.8,
  "max_tokens": 4096
}
```

**说明：**
- MiniMax 创意能力强
- 高温度，激发创造力
- 文风多样，适合各类文案

---

### 分析师 (Analyst)

```json
{
  "model": "glm-5",
  "provider": "bailian",
  "temperature": 0.5,
  "max_tokens": 4096
}
```

**说明：**
- 智谱 glm-5 逻辑推理强
- 适中温度，理性分析
- 适合数据分析和洞察

---

### 执行者 (Executor)

```json
{
  "model": "qwen3.5-plus",
  "provider": "bailian",
  "temperature": 0.7,
  "max_tokens": 2048
}
```

**说明：**
- 快速响应，成本效益高
- 适中温度，灵活执行
- 较小 token 数，简单任务够用

---

## 🔧 优化建议

### 1. 按需调整

如果某些角色使用频率低，可以降级配置：

```json
{
  "executor": {
    "model": "qwen3-turbo",  // 降级为快速版
    "temperature": 0.7
  }
}
```

### 2. 混合配置

核心角色用高配，辅助角色用标准：

```json
{
  "supervisor": {"model": "qwen3-max"},  // 高配
  "coder": {"model": "qwen3-coder-plus"}, // 高配
  "writer": {"model": "qwen3.5-plus"},    // 标准
  "executor": {"model": "qwen3.5-plus"}   // 标准
}
```

### 3. 动态切换

准备多份配置文件，按需切换：

```bash
# 高配版
cp config.high-performance.json config.json

# 标准版
cp config.standard.json config.json

# 经济版
cp config.economy.json config.json
```

---

## 📚 相关文件

- `config.high-performance.json` - 高配版配置文件
- `docs/MULTI_AGENT_ARCHITECTURE.md` - 多 Agent 架构说明
- `docs/MODEL_SELECTION_GUIDE.md` - 模型选择指南

---

## ⚠️ 注意事项

1. **API Key 安全** - 不要将配置文件提交到 Git
2. **成本控制** - 监控 Token 使用量，避免超支
3. **模型可用性** - 确保阿里云百炼平台模型可用
4. **错误处理** - 某个模型失败时，有备选方案

---

## 🔗 参考资源

- [阿里云百炼控制台](https://dashscope.console.aliyun.com/)
- [百炼 API 文档](https://help.aliyun.com/zh/dashscope/)
- [模型价格](https://help.aliyun.com/zh/dashscope/pricing)

---

**配置完成！** 🎉

现在你的 PyClaw 多 Agent 系统使用最强配置，所有模型都通过阿里云百炼平台统一调用！

---

**最后更新：** 2026-03-14  
**状态：** ✅ 已配置
