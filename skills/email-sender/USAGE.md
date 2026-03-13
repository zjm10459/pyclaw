# Email Skill 使用指南

## ✅ 已完成

| 项目 | 状态 |
|------|------|
| Skill 安装 | ✅ 已安装到 `~/.openclaw/skills/email-sender` |
| 邮箱配置 | ✅ QQ 邮箱已配置 (1045935055@qq.com) |
| 功能测试 | ✅ 邮件发送成功 |
| 配置文件 | ✅ 已保存并设置权限 (600) |

## 📚 可用工具

在 OpenClaw 中可以直接调用以下工具：

### 1. send_email - 发送邮件

**用途：** 发送电子邮件，支持附件、HTML、抄送等功能

**参数：**
- `to` (必填): 收件人邮箱，多个用逗号分隔
- `subject` (必填): 邮件主题
- `body` (必填): 邮件正文
- `html` (可选): 是否为 HTML 格式，默认 false
- `attachment` (可选): 附件路径，多个用逗号分隔
- `cc` (可选): 抄送邮箱
- `bcc` (可选): 密送邮箱
- `provider` (可选): 邮箱服务商，默认使用配置的

**示例：**
```
发送简单邮件
to=zhaojianmin3@h-partners.com
subject=会议通知
body=明天上午 10 点开会，请准时参加。

发送 HTML 邮件带附件
to=zhaojianmin3@h-partners.com
subject=PyClaw 项目
body=<h2>项目说明</h2><p>请查收附件...</p>
html=true
attachment=/home/zjm/.openclaw/workspace/pyclaw-project.zip

抄送给多人
to=dev@company.com
cc=manager@company.com,boss@company.com
subject=进度报告
body=本周完成...
```

### 2. configure_email - 配置邮箱

**用途：** 配置 SMTP 邮箱账户

**参数：**
- `provider` (必填): 邮箱服务商 (qq/gmail/163/company)
- `email` (必填): 邮箱地址
- `password` (必填): 授权码或密码
- `smtp_server` (可选): SMTP 服务器
- `smtp_port` (可选): SMTP 端口
- `use_tls` (可选): 是否使用 TLS

**示例：**
```
配置 QQ 邮箱
provider=qq
email=1045935055@qq.com
password=授权码
```

### 3. test_email - 测试邮件

**用途：** 发送测试邮件验证配置

**参数：**
- `to` (可选): 收件人邮箱，默认发送到配置的邮箱

**示例：**
```
测试邮件
to=zhaojianmin3@h-partners.com
```

### 4. list_email_accounts - 列出邮箱

**用途：** 查看已配置的邮箱账户

**参数：** 无

### 5. delete_email_account - 删除邮箱

**用途：** 删除已配置的邮箱账户

**参数：**
- `provider` (必填): 邮箱服务商

## 🎯 常用场景

### 场景 1：发送项目文件

```
send_email(
    to="zhaojianmin3@h-partners.com",
    subject="项目交付",
    body="您好，这是项目文件，请查收。",
    attachment="/path/to/project.zip"
)
```

### 场景 2：发送 HTML 报告

```
send_email(
    to="boss@company.com",
    subject="月度报告",
    body="<h1>月度报告</h1><h2>完成情况</h2><ul><li>任务 1: ✅</li><li>任务 2: ✅</li></ul>",
    html=true
)
```

### 场景 3：群发通知

```
send_email(
    to="team@company.com",
    cc="manager@company.com",
    subject="放假通知",
    body="各位同事，明天放假一天..."
)
```

### 场景 4：发送多个附件

```
send_email(
    to="client@example.com",
    subject="项目文档",
    body="请查收项目文档",
    attachment="/path/to/doc1.pdf,/path/to/doc2.zip"
)
```

## 📁 文件结构

```
~/.openclaw/skills/email-sender/
├── SKILL.md           # Skill 说明文档
├── README.md          # 使用手册
├── USAGE.md           # 本文件
├── install.sh         # 安装脚本
├── email_skill.py     # OpenClaw 工具包装器
├── email_tools.py     # 核心邮件工具
├── tools.json         # 工具定义
├── config.json        # 邮箱配置（权限 600）
└── __pycache__/       # Python 缓存
```

## 🔧 维护

### 更新配置

编辑 `~/.openclaw/skills/email-sender/config.json`

### 查看日志

邮件发送日志会显示在 OpenClaw 的控制台输出中。

### 卸载 Skill

```bash
rm -rf ~/.openclaw/skills/email-sender
```

## ⚠️ 注意事项

1. **授权码安全**
   - 配置文件权限已设置为 600（仅所有者可读写）
   - 不要将配置文件提交到 Git
   - 建议使用应用专用密码

2. **发送限制**
   - QQ 邮箱：每天最多 500 封
   - Gmail：每天最多 500 封
   - 避免短时间内大量发送

3. **附件大小**
   - 大多数邮箱服务商限制 25MB
   - 大文件建议使用云存储链接

## 📞 支持

如有问题，请联系：
- 作者：zjm
- 邮箱：zhaojianmin3@h-partners.com
