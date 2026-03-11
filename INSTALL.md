# PyClaw 安装指南

## 快速安装

### 基础安装（推荐）

```bash
# 克隆仓库
git clone https://github.com/pyclaw/pyclaw.git
cd pyclaw

# 安装依赖
pip install -e .
```

### 完整安装（包含所有功能）

```bash
pip install -e ".[all]"
```

## 安装选项

### 1. 基础安装

只安装核心依赖：

```bash
pip install -e .
```

**包含：**
- LangChain 核心
- WebSocket 支持
- 基础工具
- RAG 记忆系统

### 2. 性能优化

添加性能优化依赖：

```bash
pip install -e ".[performance]"
```

**包含：**
- FAISS 向量检索（5-100 倍加速）
- orjson 快速 JSON 解析

### 3. 渠道集成

添加额外渠道支持：

```bash
pip install -e ".[channels]"
```

**包含：**
- Telegram Bot
- Discord.py

### 4. 开发工具

添加开发和测试工具：

```bash
pip install -e ".[dev]"
```

**包含：**
- pytest（测试框架）
- black（代码格式化）
- mypy（类型检查）
- sphinx（文档生成）

### 5. 完整安装

安装所有依赖：

```bash
pip install -e ".[all]"
```

**包含：**
- 所有性能优化
- 所有渠道集成
- 所有开发工具

## 环境要求

- **Python:** 3.10, 3.11, 3.12
- **操作系统:** Linux, macOS, Windows
- **内存:** 最少 2GB（推荐 4GB+）

## 验证安装

```bash
# 检查版本
pyclaw --version

# 运行测试
pytest tests/ -v

# 启动服务器
pyclaw start
```

## 配置环境变量

创建 `.env` 文件：

```bash
# LLM Provider API Keys
export DASHSCOPE_API_KEY="your-dashscope-key"
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"

# 可选：自定义配置
export PYCLAW_WORKSPACE="~/.pyclaw"
export PYCLAW_LOG_LEVEL="INFO"
```

## 故障排查

### 问题 1: 依赖冲突

**症状：**
```
ERROR: Cannot install pyclaw and langchain-core==0.2.0
```

**解决方案：**
```bash
# 升级 pip
pip install --upgrade pip

# 清理缓存
pip cache purge

# 重新安装
pip install -e . --force-reinstall
```

### 问题 2: FAISS 安装失败

**症状：**
```
ERROR: Could not build wheels for faiss-cpu
```

**解决方案：**

**Linux/macOS:**
```bash
# 使用 conda（推荐）
conda install -c pytorch faiss-cpu

# 或使用预编译包
pip install faiss-cpu --only-binary :all:
```

**Windows:**
```bash
# 使用预编译包
pip install faiss-cpu --only-binary :all:
```

### 问题 3: sentence-transformers 安装失败

**症状：**
```
ERROR: Failed building wheel for sentence-transformers
```

**解决方案：**
```bash
# 安装构建工具
pip install wheel setuptools

# 或使用预编译包
pip install sentence-transformers --only-binary :all:
```

## 卸载

```bash
# 卸载 PyClaw
pip uninstall pyclaw

# 清理配置
rm -rf ~/.pyclaw
```

## 从源代码安装

```bash
# 克隆仓库
git clone https://github.com/pyclaw/pyclaw.git
cd pyclaw

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/ -v

# 构建文档
cd docs
make html
```

## Docker 安装（可选）

```bash
# 构建镜像
docker build -t pyclaw:latest .

# 运行容器
docker run -it pyclaw:latest
```

## 下一步

安装完成后，查看：
- [快速启动指南](QUICKSTART.md)
- [配置说明](config/README.md)
- [使用文档](docs/README.md)

---

_最后更新：2026-03-11_
