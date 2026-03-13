# Email Sender Skill 📧

OpenClaw 邮件发送 Skill，支持通过 SMTP 发送带附件的 HTML 邮件。

## 安装

```bash
cd /home/zjm/.openclaw/workspace/skills/email-sender
bash install.sh
```

## 快速开始

### 1. 配置邮箱

首次使用需要配置 SMTP 邮箱账户：

```python
# 在 OpenClaw 中调用
configure_email(
    provider="qq",
    email="1045935055@qq.com",
    password="你的授权码"
)
```

**支持的邮箱服务商：**

| 服务商 | provider | 说明 |
|--------|----------|------|
| QQ 邮箱 | `qq` | 需要授权码 |
| Gmail | `gmail` | 需要应用专用密码 |
| 163 邮箱 | `163` | 需要授权码 |
| 公司邮箱 | `company` | 自定义 SMTP |

### 2. 发送邮件

```python
# 发送简单邮件
send_email(
    to="zhaojianmin3@h-partners.com",
    subject="项目报告",
    body="请查收附件"
)

# 发送 HTML 邮件带附件
send_email(
    to="zhaojianmin3@h-partners.com",
    subject="PyClaw 项目",
    body="<h2>项目说明</h2><p>详细内容...</p>",
    html=True,
    attachment="/path/to/file.zip"
)

# 抄送给多人
send_email(
    to="dev@company.com",
    cc="manager@company.com,boss@company.com",
    subject="进度报告",
    body="本周完成..."
)
```

### 3. 测试邮件

```python
# 发送测试邮件
test_email(to="zhaojianmin3@h-partners.com")
```

### 4. 管理账户

```python
# 列出已配置的邮箱
list_email_accounts()

# 删除邮箱配置
delete_email_account(provider="qq")
```

## 工具列表

| 工具名 | 说明 |
|--------|------|
| `send_email` | 发送邮件（支持附件、HTML、抄送） |
| `configure_email` | 配置 SMTP 邮箱账户 |
| `test_email` | 测试邮件发送 |
| `list_email_accounts` | 列出已配置的邮箱 |
| `delete_email_account` | 删除邮箱配置 |

## 配置存储

配置文件位置：`~/.openclaw/skills/email-sender/config.json`

配置示例：
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

## 获取授权码

### QQ 邮箱
1. 登录 QQ 邮箱网页版
2. 设置 → 账户
3. 开启 "POP3/SMTP 服务"
4. 生成授权码

### Gmail
1. 开启两步验证
2. 访问 https://myaccount.google.com/apppasswords
3. 生成应用专用密码

### 163 邮箱
1. 登录 163 邮箱网页版
2. 设置 → POP3/SMTP/IMAP
3. 开启 "IMAP/SMTP 服务"
4. 获取授权码

## 安全提示

- ⚠️ 授权码存储在本地配置文件中
- ⚠️ 配置文件权限设置为 600（仅所有者可读写）
- ⚠️ 不要将配置文件提交到版本控制
- ✅ 建议使用应用专用密码，而不是主密码

## 故障排除

### 认证失败
- 检查是否使用授权码（不是登录密码）
- 确认 SMTP 服务已开启

### 连接超时
- 检查防火墙设置
- 尝试端口 465（SSL）代替 587（TLS）

### 附件发送失败
- 检查文件路径是否正确
- 确保文件存在且可读
- 注意附件大小限制（通常 25MB）

## 版本

v1.0.0 (2026-03-04)

## 作者

zjm <zhaojianmin3@h-partners.com>
