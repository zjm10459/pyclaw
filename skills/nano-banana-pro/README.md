# Nano Banana Pro Skill

这是从 ClawHub 安装的 Nano Banana Pro 技能，用于使用 Gemini 3 Pro Image 模型生成和编辑图像。

## 安装位置

```
skills/nano-banana-pro/
├── SKILL.md           # 技能定义和使用说明
├── README.md          # 本文件
├── .clawhub/
│   └── lock.json      # 安装元数据
└── scripts/
    ├── generate.py    # 文生图脚本
    └── edit.py        # 图像编辑脚本
```

## 前置要求

1. **Python 3.10+**
2. **安装依赖包**：
   ```bash
   pip install google-genai pillow
   # 或使用 uv
   uv pip install google-genai pillow
   ```

3. **设置 API Key**：
   ```bash
   # 获取 API Key: https://aistudio.google.com/app/apikey
   export GEMINI_API_KEY=your_api_key_here
   ```

## 使用方法

### 文生图

```bash
# 基本用法
python skills/nano-banana-pro/scripts/generate.py \
  --prompt "A sunset over mountains" \
  --output sunset.png

# 指定分辨率 (1K, 2K, 4K)
python skills/nano-banana-pro/scripts/generate.py \
  --prompt "A beautiful landscape" \
  --resolution 4K \
  --output landscape.png

# 指定 API Key
python skills/nano-banana-pro/scripts/generate.py \
  --prompt "Test image" \
  --api-key YOUR_API_KEY \
  --output test.png
```

### 图像编辑

```bash
# 编辑现有图像
python skills/nano-banana-pro/scripts/edit.py \
  --input-image photo.jpg \
  --prompt "Add sunglasses to the person" \
  --output edited.png

# 背景替换
python skills/nano-banana-pro/scripts/edit.py \
  --input-image portrait.png \
  --prompt "Remove background and add sunset" \
  --output portrait_bg.png

# 风格转换
python skills/nano-banana-pro/scripts/edit.py \
  --input-image photo.jpg \
  --prompt "Convert to anime style" \
  --output anime.png
```

## 分辨率选项

| 分辨率 | 尺寸 | 用途 | 预估时间 |
|--------|------|------|----------|
| 1K | 1024x1024 | 快速预览、缩略图 | ~5 秒 |
| 2K | 2048x2048 | 标准质量图像 | ~10 秒 |
| 4K | 4096x4096 | 高质量详细图像 | ~20 秒 |

## 常见问题

### 获取 API Key
访问 [Google AI Studio](https://aistudio.google.com/app/apikey) 获取免费的 Gemini API Key。

### 定价
- Google 提供一定的免费额度
- 超出后按使用量计费
- 4K 图像价格较高，建议先用 1K 或 2K 测试

### 错误处理
- 如果看到 `google-genai package not installed`，运行 `pip install google-genai`
- 如果看到 `No API key provided`，设置 `GEMINI_API_KEY` 环境变量或使用 `--api-key` 参数

## 更多信息

- 原始技能页面：https://clawhub.ai/steipete/nano-banana-pro
- 发布者：Peter Steinberger (@steipete)
- 许可证：MIT-0
