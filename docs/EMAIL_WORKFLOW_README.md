# 📧 邮件发送工作流文档

> 完整的结构化文档生成和邮件发送解决方案

---

## 📁 文档结构

```
docs/
├── EMAIL_WORKFLOW_README.md        # 本文件 - 总览
├── 结构化文档模板.md                # Markdown 文档模板
├── 邮件发送配置指南.md              # 详细配置指南
├── 邮件发送快速入门.md              # 5 分钟快速开始
└── templates/
    └── document_notification.html   # 邮件 HTML 模板

config/
└── email_config.example.json        # 邮件配置示例

tools/
├── send_document_email.py           # 文档邮件发送工具
└── email_workflow.py                # 邮件工作流自动化脚本
```

---

## 🎯 功能特性

### ✅ 结构化文档模板
- 完整的 Markdown 文档结构
- 包含目录、元信息、变更记录等
- 支持 Mermaid 图表
- 内置任务清单和时间线

### ✅ 邮件发送配置
- 支持多种 SMTP 服务（QQ、Gmail、163、企业邮箱）
- 支持 HTML 和纯文本邮件
- 支持附件、抄送、密送
- 安全的凭据管理

### ✅ 自动化工具
- **文档通知工具**：自动提取文档信息并发送通知
- **工作流脚本**：4 种预定义场景
  - 文档发布通知
  - 周报自动发送
  - 项目更新通知
  - 告警邮件发送

### ✅ HTML 邮件模板
- 响应式设计
- 美观的渐变头部
- 结构化内容展示
- 可自定义扩展

---

## 🚀 快速开始

### 1. 配置邮箱

```bash
# 复制示例配置
cp config/email_config.example.json config/email_config.json

# 编辑配置（填入你的邮箱信息）
vim config/email_config.json
```

### 2. 测试发送

```bash
# 模拟发送（不实际发出）
python tools/email_workflow.py alert \
  --to "test@example.com" \
  --title "测试" \
  --message "测试邮件" \
  --dry-run

# 实际发送
python tools/email_workflow.py alert \
  --to "test@example.com" \
  --title "测试" \
  --message "测试邮件"
```

### 3. 发送文档通知

```bash
python tools/email_workflow.py doc-notify \
  --to team@company.com \
  --doc "./docs/项目计划.md" \
  --cc manager@company.com
```

---

## 📖 详细文档

| 文档 | 用途 | 阅读时间 |
|------|------|----------|
| [邮件发送快速入门.md](./邮件发送快速入门.md) | 5 分钟快速开始 | 5 分钟 |
| [邮件发送配置指南.md](./邮件发送配置指南.md) | 完整配置说明 | 15 分钟 |
| [结构化文档模板.md](./结构化文档模板.md) | 文档编写规范 | 10 分钟 |

---

## 🛠️ 工具说明

### send_document_email.py

**用途：** 发送文档发布通知邮件

**功能：**
- 自动提取 Markdown 文档元信息
- 使用 HTML 模板美化邮件
- 支持附件发送
- 支持抄送和密送

**使用示例：**
```bash
python tools/send_document_email.py \
  --to recipient@example.com \
  --doc-title "项目计划书" \
  --doc-path "./docs/项目计划书.md" \
  --author "张三" \
  --tags "项目" "计划" "2026"
```

### email_workflow.py

**用途：** 邮件发送工作流自动化

**支持场景：**
1. `doc-notify` - 文档发布通知
2. `weekly-report` - 周报发送
3. `project-update` - 项目更新
4. `alert` - 告警邮件

**使用示例：**
```bash
# 发送周报
python tools/email_workflow.py weekly-report \
  --to manager@company.com \
  --week "2026-W11" \
  --completed "需求分析" "系统设计" \
  --planned "编码实现" "单元测试"

# 发送告警
python tools/email_workflow.py alert \
  --to oncall@company.com \
  --title "系统异常" \
  --message "API 响应超时" \
  --level error
```

---

## 🔐 安全最佳实践

### 1. 保护配置文件

```bash
# 将配置文件添加到 .gitignore
echo "config/email_config.json" >> .gitignore

# 设置文件权限
chmod 600 config/email_config.json
```

### 2. 使用环境变量

```bash
# .env 文件
SMTP_PASSWORD=your_auth_code_here

# Python 代码中读取
import os
password = os.getenv('SMTP_PASSWORD')
```

### 3. 使用授权码

- ❌ 不要使用登录密码
- ✅ 使用邮箱服务商提供的授权码
- ✅ 定期更换授权码（3-6 个月）

---

## 📊 配置示例

### 最小配置

```json
{
  "email": {
    "smtp_server": "smtp.qq.com",
    "smtp_port": 465,
    "smtp_user": "your_email@qq.com",
    "smtp_password": "YOUR_AUTH_CODE",
    "use_ssl": true
  }
}
```

### 完整配置

```json
{
  "email": {
    "smtp_server": "smtp.qq.com",
    "smtp_port": 465,
    "smtp_user": "notifications@company.com",
    "smtp_password": "YOUR_AUTH_CODE",
    "use_ssl": true,
    "use_tls": false,
    "timeout": 30,
    "retry_count": 3
  },
  "defaults": {
    "from_name": "PyClaw 通知系统",
    "encoding": "utf-8",
    "reply_to": "support@company.com"
  },
  "templates": {
    "document_notification": {
      "subject": "文档发布：{doc_title}",
      "body_template": "docs/templates/document_notification.html"
    },
    "weekly_report": {
      "subject": "周报 - {week}",
      "body_template": "docs/templates/weekly_report.html"
    }
  },
  "recipients": {
    "team": ["member1@company.com", "member2@company.com"],
    "management": ["manager@company.com"],
    "all_staff": ["all@company.com"]
  }
}
```

---

## 🔧 故障排查

### 常见问题速查

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 认证失败 | 密码错误/服务未开启 | 检查授权码，开启 SMTP 服务 |
| 连接超时 | 网络/防火墙 | 检查网络，确认端口开放 |
| 配置不存在 | 文件路径错误 | 确认配置文件存在 |
| 附件过大 | 超过邮件大小限制 | 使用云存储链接 |

### 调试模式

```bash
# 使用 --dry-run 查看邮件内容
python tools/email_workflow.py alert \
  --to test@example.com \
  --title "测试" \
  --message "内容" \
  --dry-run

# 查看详细错误
python -c "
import smtplib
server = smtplib.SMTP_SSL('smtp.qq.com', 465)
server.login('your_email@qq.com', 'your_auth_code')
print('连接成功')
server.quit()
"
```

---

## 📚 扩展开发

### 添加新的工作流

1. 在 `EmailWorkflow` 类中添加新方法
2. 在 `main()` 函数中添加命令行参数
3. 创建对应的 HTML 模板（可选）

### 自定义邮件模板

1. 在 `docs/templates/` 创建 HTML 文件
2. 使用 `{{variable}}` 语法定义变量
3. 在配置文件中引用模板

### 集成到 CI/CD

```yaml
# GitHub Actions 示例
- name: Send notification email
  run: |
    python tools/email_workflow.py alert \
      --to team@company.com \
      --title "部署完成" \
      --message "版本 ${VERSION} 已部署" \
      --level info
  env:
    SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}
```

---

## 📝 更新日志

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2026-03-14 | 初始版本，包含完整功能 |

---

## 🤝 支持

如有问题，请查阅：
1. [快速入门指南](./邮件发送快速入门.md)
2. [详细配置指南](./邮件发送配置指南.md)
3. 检查错误日志

---

*文档创建：2026-03-14 | 阿紫*
