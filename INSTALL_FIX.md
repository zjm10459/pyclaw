# PyClaw 安装问题修复

## 问题总结

### 问题 1: pyproject.toml 配置错误

**错误信息：**
```
error: package directory 'pyclaw' does not exist
```

**原因：**
- `pyproject.toml` 中配置 `packages = ["pyclaw"]`
- 但代码是扁平结构，直接在根目录
- setuptools 寻找 `pyclaw/pyclaw/` 目录但找不到

**解决方案：**
```toml
[tool.setuptools.packages.find]
where = ["."]
include = ["agents*", "channels*", "config*", "gateway*", "memory*", "scheduler*", "sessions*", "skills*", "tests*", "tools*", "utils*"]
```

---

### 问题 2: License 配置冲突

**错误信息：**
```
License classifiers have been superseded by license expressions
Please remove: License :: OSI Approved :: MIT License
```

**原因：**
- setuptools 77+ 使用 SPDX license 表达式
- 旧的 license classifier 与新格式冲突

**解决方案：**
```toml
# 旧配置（错误）
license = {text = "MIT"}
classifiers = [
    "License :: OSI Approved :: MIT License",  # 冲突
]

# 新配置（正确）
license = "MIT"
classifiers = [
    # 移除 license classifier
]
```

---

### 问题 3: UV 配置文件格式错误

**错误信息：**
```
TOML parse error at line 10, column 3
duplicate key
```

**原因：**
- 重复定义了 `[[index]]`
- 使用了 UV 不支持的字段

**解决方案：**
```toml
# 正确的 UV 配置
index-url = "https://pypi.tuna.tsinghua.edu.cn/simple"
concurrent-downloads = 10
concurrent-installs = 5
```

---

## ✅ 修复结果

### 安装成功

```bash
uv sync
# ✓ Building pyclaw @ file:///home/zjm/.openclaw/workspace/pyclaw
# ✓ Prepared 5 packages in 3m 57s
# ✓ Installed 114 packages in 355ms
```

### 安装的包

- langchain==1.2.11
- langchain-anthropic==1.3.4
- langchain-classic==1.0.2
- aiohttp==3.13.3
- beautifulsoup4==4.14.3
- click==8.3.1
- pydantic==2.x
- sentence-transformers==2.x
- ... 共 114 个包

---

## 📝 正确的 pyproject.toml 结构

```toml
[project]
name = "pyclaw"
version = "2.0.0"
license = "MIT"  # SPDX 表达式

classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    # 不要包含 License classifier
]

[tool.setuptools.packages.find]
where = ["."]
include = ["agents*", "channels*", ...]
```

---

## 🔧 安装步骤

### 1. 清理缓存

```bash
cd /home/zjm/.openclaw/workspace/pyclaw
rm -rf .venv/ __pycache__/ *.egg-info/
uv cache clean
```

### 2. 安装依赖

```bash
uv sync
```

### 3. 验证安装

```bash
# 检查 Python 版本
python --version

# 检查主要包
python -c "import langchain; print(langchain.__version__)"
python -c "import pyclaw; print('PyClaw installed!')"
```

---

## ⚠️ 常见错误及解决方案

### 错误 1: package directory does not exist

```bash
# 检查 pyproject.toml
cat pyproject.toml | grep -A 5 "packages.find"

# 确保使用扁平结构配置
[tool.setuptools.packages.find]
where = ["."]
```

### 错误 2: License classifiers deprecated

```bash
# 移除 license classifier
# 编辑 pyproject.toml，删除：
# "License :: OSI Approved :: MIT License"
```

### 错误 3: TOML parse error

```bash
# 检查 TOML 语法
uv pip compile pyproject.toml

# 或使用在线工具验证
# https://toml.io/
```

---

## 📊 安装统计

| 项目 | 数量 |
|------|------|
| 总包数 | 171 |
| 安装包数 | 114 |
| 下载大小 | ~2.5GB |
| 安装时间 | ~4 分钟 |
| Python 版本 | 3.13.12 |

---

## 🎯 下一步

### 1. 测试安装

```bash
python main.py --help
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填写 API Key
```

### 3. 运行测试

```bash
pytest tests/ -v
```

---

## 📚 参考文档

- [PEP 639 - License Field](https://peps.python.org/pep-0639/)
- [setuptools pyproject.toml](https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html)
- [UV 配置文档](https://docs.astral.sh/uv/)

---

_修复时间：2026-03-11_
_PyClaw Team_
