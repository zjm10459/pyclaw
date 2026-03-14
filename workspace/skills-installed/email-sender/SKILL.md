---
name: email-sender
description: 通过 SMTP 发送邮件，支持附件、HTML、抄送等功能。使用 QQ 邮箱、Gmail、公司邮箱等常见 SMTP 服务。
homepage: https://github.com/openclaw/openclaw/tree/main/skills/email-sender
metadata:
  {
    "openclaw":
      {
        "emoji": "📧",
        "requires": { "bins": ["python3"], "env": [] },
        "install":
          [
            {
              "id": "python-pip",
              "kind": "pip",
              "packages": [],
              "label": "Python 环境（内置 smtplib，无需额外依赖）",
            },
          ],
      },
  }
---

# Email Sender Skill 📧

通过 SMTP 发送邮件的 Skill，支持多种邮箱服务商。

## 何时使用

✅ **使用此技能当：**

- 需要发送通知邮件、报告、提醒
- 需要发送带附件的邮件
- 需要抄送/密送给多人
- 需要发送 HTML 格式邮件

❌ **不要使用此技能当：**

- 需要发送批量营销邮件（使用专业邮件服务）
- 需要邮件模板管理（使用邮件营销平台）
- 需要邮件追踪分析（使用 SendGrid/Mailgun 等）

## 快速开始

### 1. 首次配置邮箱

```bash
python3 {baseDir}/scripts/send_email.py configure --provider qq --email 1045935055@qq.com --password 授权码
```

**支持的邮箱服务商：**

| 服务商 | SMTP 服务器 | 端口 | 说明 |
|--------|------------|------|------|
| QQ 邮箱 | smtp.qq.com | 587 | 需要授权码 |
| Gmail | smtp.gmail.com | 587 | 需要应用专用密码 |
| 163 邮箱 | smtp.163.com | 587 | 需要授权码 |
| 公司邮箱 | 自定义 | 587/465 | 咨询公司 IT 部门 |

**获取授权码：**
- QQ 邮箱：设置 → 账户 → 开启 SMTP 服务 → 生成授权码
- Gmail：开启两步验证 → 生成应用专用密码

### 2. 发送简单邮件

```bash
python3 {baseDir}/scripts/send_email.py send --to user@example.com --subject "问候" --body "你好，这是一封测试邮件"
```

### 3. 发送 HTML 邮件

```bash
python3 {baseDir}/scripts/send_email.py send --to user@example.com --subject "通知" --body "<h1>标题</h1><p>内容</p>" --html
```

### 4. 发送带附件的邮件

```bash
python3 {baseDir}/scripts/send_email.py send --to boss@company.com --subject "项目汇报" --body "请查收附件" --attachment /path/to/report.pdf
```

### 5. 抄送/密送

```bash
python3 {baseDir}/scripts/send_email.py send --to dev@company.com --subject "进度报告" --body "本周完成..." --cc manager@company.com,boss@company.com
```

### 6. 测试邮件

```bash
python3 {baseDir}/scripts/send_email.py test --to zhaojianmin3@h-partners.com
```

### 7. 查看已配置账户

```bash
python3 {baseDir}/scripts/send_email.py list
```

### 8. 删除账户

```bash
python3 {baseDir}/scripts/send_email.py delete --provider qq
```

## 命令参考

### configure - 配置邮箱

```bash
python3 {baseDir}/scripts/send_email.py configure \
  --provider <qq|gmail|163|company> \
  --email <邮箱地址> \
  --password <授权码/密码> \
  [--smtp-server <SMTP 服务器>] \
  [--smtp-port <端口>] \
  [--no-tls]
```

**参数：**
- `--provider, -p`: 邮箱服务商（必填）
- `--email, -e`: 邮箱地址（必填）
- `--password, -P`: 授权码/密码（必填）
- `--smtp-server, -s`: SMTP 服务器（可选，自动匹配）
- `--smtp-port, -S`: SMTP 端口（可选，自动匹配）
- `--no-tls`: 不使用 TLS（可选）

### send - 发送邮件

```bash
python3 {baseDir}/scripts/send_email.py send \
  --to <收件人> \
  --subject <主题> \
  --body <正文> \
  [--html] \
  [--attachment <附件路径>] \
  [--cc <抄送>] \
  [--bcc <密送>] \
  [--provider <服务商>]
```

**参数：**
- `--to, -t`: 收件人邮箱（必填，多个用逗号分隔）
- `--subject, -subj`: 邮件主题（必填）
- `--body, -b`: 邮件正文（必填）
- `--html`: 是否为 HTML 格式（可选，默认 false）
- `--attachment, -a`: 附件路径（可选，多个用逗号分隔）
- `--cc`: 抄送邮箱（可选，多个用逗号分隔）
- `--bcc`: 密送邮箱（可选，多个用逗号分隔）
- `--provider, -p`: 使用的邮箱服务商（可选，默认配置的）

### test - 测试邮件

```bash
python3 {baseDir}/scripts/send_email.py test [--to <收件人>]
```

**参数：**
- `--to, -t`: 收件人邮箱（可选，默认发送到配置的邮箱）

### list - 列出账户

```bash
python3 {baseDir}/scripts/send_email.py list
```

### delete - 删除账户

```bash
python3 {baseDir}/scripts/send_email.py delete --provider <qq|gmail|163|company>
```

## 输出格式

所有命令输出 JSON 格式结果，便于 AI 解析：

**成功示例：**
```json
{
  "success": true,
  "message": "✓ 邮件已发送到：user@example.com",
  "to": ["user@example.com"],
  "cc": null,
  "attachments": 1
}
```

**失败示例：**
```json
{
  "success": false,
  "error": "SMTP 认证失败，请检查邮箱账号和授权码"
}
```

## 配置存储

配置保存在：`~/.openclaw/skills/email-sender/config.json`

配置内容示例：
```json
{
  "default_provider": "qq",
  "accounts": {
    "qq": {
      "email": "1045935055@qq.com",
      "password": "授权码",
      "smtp_server": "smtp.qq.com",
      "smtp_port": 587,
      "use_tls": true
    }
  }
}
```

## 常见问题

### 1. 认证失败
- 检查是否使用授权码（不是登录密码）
- QQ 邮箱：设置→账户→开启 SMTP 服务→生成授权码
- Gmail：需要开启两步验证，然后生成应用专用密码

### 2. 连接超时
- 检查防火墙设置
- 尝试使用端口 465（SSL）代替 587（TLS）

### 3. 附件发送失败
- 检查文件路径是否正确
- 确保文件存在且可读
- 注意附件大小限制（通常 25MB）

### 4. HTML 邮件乱码
- 确保 `--html` 参数正确设置
- HTML 内容使用 UTF-8 编码
- 避免使用特殊字符或转义

## 安全提示

- ⚠️ 授权码/密码存储在本地配置文件中
- ⚠️ 配置文件权限设置为 600（仅所有者可读写）
- ⚠️ 不要将配置文件提交到版本控制
- ✅ 建议使用应用专用密码，而不是主密码
- ✅ 定期更换授权码

## 更新日志

- v1.0.0 (2026-03-04) - 初始版本
  - 支持 SMTP 邮件发送
  - 支持附件、HTML、抄送
  - 支持多种邮箱服务商
- v1.1.0 (2026-03-14) - 改为 OpenClaw 模式
  - 从工具注册改为 exec 调用
  - 支持命令行参数
  - JSON 输出便于 AI 解析
