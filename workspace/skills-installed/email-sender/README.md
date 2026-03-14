# Email Sender Skill - OpenClaw 模式 📧

## 改造说明

本技能已从 **PyClaw 工具模式** 改造为 **OpenClaw exec 模式**。

### 改造前后对比

| 方面 | 改造前（PyClaw） | 改造后（OpenClaw） |
|------|-----------------|-------------------|
| 工具注册 | 注册到 ToolRegistry | ❌ 不再注册 |
| 调用方式 | `tool_registry.call("send_email", ...)` | `exec("python3 scripts/send_email.py send ...")` |
| 文件结构 | `email_tools.py` | `scripts/send_email.py` |
| 参数传递 | Python 函数参数 | 命令行参数 |
| 返回值 | Python 对象 | JSON (stdout) |
| AI 调用 | 直接调用工具 | 通过 exec 工具执行 |

### 文件结构

```
skills/email-sender/
├── SKILL.md              # 技能文档（AI 阅读）
├── README.md             # 本文件
└── scripts/
    └── send_email.py     # 可执行脚本
```

### 使用示例

#### 1. AI 调用示例（通过 exec 工具）

AI 看到 SKILL.md 后，会执行：

```bash
# 配置邮箱
exec(command="python3 /path/to/skills/email-sender/scripts/send_email.py configure --provider qq --email 1045935055@qq.com --password AUTH_CODE")

# 发送邮件
exec(command="python3 /path/to/skills/email-sender/scripts/send_email.py send --to user@example.com --subject '测试' --body '你好'")

# 测试邮件
exec(command="python3 /path/to/skills/email-sender/scripts/send_email.py test")

# 查看配置
exec(command="python3 /path/to/skills/email-sender/scripts/send_email.py list")
```

#### 2. 手动测试

```bash
cd /home/zjm/.openclaw/workspace/skills/email-sender

# 查看帮助
python3 scripts/send_email.py --help

# 查看已配置账户
python3 scripts/send_email.py list

# 测试邮件（发送到配置的邮箱）
python3 scripts/send_email.py test

# 发送邮件
python3 scripts/send_email.py send \
  --to 1045935055@qq.com \
  --subject "测试邮件" \
  --body "这是一封测试邮件"
```

### 输出格式

所有命令输出 JSON 格式，便于 AI 解析：

**成功：**
```json
{
  "success": true,
  "message": "✓ 邮件已发送到：user@example.com",
  "to": ["user@example.com"],
  "attachments": 0
}
```

**失败：**
```json
{
  "success": false,
  "error": "SMTP 认证失败，请检查邮箱账号和授权码"
}
```

### 配置位置

配置文件：`~/.openclaw/skills/email-sender/config.json`

### 优势

✅ **脚本独立** - 可以直接运行测试，不依赖 PyClaw 框架
✅ **易于调试** - 命令行参数清晰，stdout 直接看到结果
✅ **跨框架** - 可以在任何 Python 环境中使用
✅ **AI 友好** - JSON 输出便于解析，错误信息清晰
✅ **符合 OpenClaw 规范** - 与其他内置技能保持一致

### 迁移指南

如果你有其他技能也想改为 OpenClaw 模式：

1. 创建 `scripts/` 目录
2. 将工具函数改为 CLI 脚本（使用 argparse）
3. 更新 SKILL.md，添加 exec 调用示例
4. 从 PyClaw 的 tool_registry 移除注册代码
5. 测试：`python3 scripts/xxx.py --help`

### 注意事项

- ⚠️ 确保脚本有执行权限：`chmod +x scripts/send_email.py`
- ⚠️ 路径使用 `{baseDir}` 占位符，AI 会自动替换
- ⚠️ 所有输出必须是 JSON 格式（便于 AI 解析）
- ⚠️ 退出码：成功=0，失败=1（便于 exec 工具判断）

---

**版本：** v1.1.0 (OpenClaw 模式)  
**最后更新：** 2026-03-14
