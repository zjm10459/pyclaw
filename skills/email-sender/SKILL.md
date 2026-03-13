---
name: email-sender
description: 通过 SMTP 发送邮件，支持附件、HTML、抄送等功能。使用 QQ 邮箱、Gmail、公司邮箱等常见 SMTP 服务。
version: 1.0.0
author: zjm
tags: [email, smtp, mail, qq-mail, notification]
metadata:
  openclaw:
    emoji: 📧
    requires:
      python: ["smtplib", "email"]
    install:
      - id: pip
        kind: pip
        packages: []
    tools:
      - name: send_email
        description: 发送邮件（支持附件、HTML、抄送）
      - name: configure_email
        description: 配置 SMTP 邮箱账户
      - name: test_email
        description: 测试邮件发送
---

# Email Sender Skill 📧

通过 SMTP 发送邮件的 Skill，支持多种邮箱服务商。

## 功能特性

- ✅ 支持多种 SMTP 服务（QQ 邮箱、Gmail、163 邮箱、公司邮箱等）
- ✅ 支持附件发送
- ✅ 支持 HTML 格式邮件
- ✅ 支持抄送（CC）和密送（BCC）
- ✅ 支持多收件人
- ✅ 配置持久化存储

## 快速开始

### 1. 首次配置

```
配置 SMTP 邮箱账户，选择服务商并填写凭据
```

**参数：**
- `provider`: 邮箱服务商（qq/gmail/163/company）
- `email`: 邮箱地址
- `password`: 授权码/密码
- `smtp_server`: SMTP 服务器（可选，自动匹配）
- `smtp_port`: SMTP 端口（可选，自动匹配）

**示例：**
```
配置邮箱 provider=qq email=1045935055@qq.com password=授权码
```

### 2. 发送邮件

```
发送邮件到指定邮箱，支持附件和 HTML 格式
```

**参数：**
- `to`: 收件人邮箱（必填，多个用逗号分隔）
- `subject`: 邮件主题（必填）
- `body`: 邮件正文（必填）
- `html`: 是否为 HTML 格式（可选，默认 false）
- `attachment`: 附件路径（可选，多个用逗号分隔）
- `cc`: 抄送邮箱（可选）
- `bcc`: 密送邮箱（可选）

**示例：**
```
发送邮件 to=zhaojianmin3@h-partners.com subject=项目报告 body=请查收附件 attachment=/path/to/file.zip

发送 HTML 邮件 to=user@example.com subject=通知 body="<h1>标题</h1><p>内容</p>" html=true
```

### 3. 测试邮件

```
发送测试邮件到指定邮箱，验证配置是否正确
```

**参数：**
- `to`: 收件人邮箱（可选，默认配置的发件人）

**示例：**
```
测试邮件 to=zhaojianmin3@h-partners.com
```

## 支持的邮箱服务商

| 服务商 | SMTP 服务器 | 端口 | 说明 |
|--------|------------|------|------|
| QQ 邮箱 | smtp.qq.com | 587 | 需要授权码 |
| Gmail | smtp.gmail.com | 587 | 需要应用专用密码 |
| 163 邮箱 | smtp.163.com | 587 | 需要授权码 |
| 公司邮箱 | 自定义 | 587/465 | 咨询公司 IT 部门 |

## 配置存储

配置保存在：`~/.openclaw/skills/email-sender/config.json`

配置内容：
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

## 使用示例

### 发送简单邮件
```
发送邮件 to=user@example.com subject=问候 body=你好，这是一封测试邮件
```

### 发送带附件的邮件
```
发送邮件 to=boss@company.com subject=项目汇报 body=请查收附件 attachment=/path/to/report.pdf
```

### 发送 HTML 邮件
```
发送邮件 to=team@company.com subject=会议通知 body="<h2>会议通知</h2><p>时间：明天 10 点</p><p>地点：会议室 A</p>" html=true
```

### 抄送给多人
```
发送邮件 to=dev@company.com cc=manager@company.com,boss@company.com subject=进度报告 body=本周完成...
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

## 安全提示

- ⚠️ 授权码/密码存储在本地配置文件中
- ⚠️ 配置文件权限设置为 600（仅所有者可读写）
- ⚠️ 不要将配置文件提交到版本控制
- ✅ 建议使用应用专用密码，而不是主密码

## 更新日志

- v1.0.0 (2026-03-04) - 初始版本
  - 支持 SMTP 邮件发送
  - 支持附件、HTML、抄送
  - 支持多种邮箱服务商
