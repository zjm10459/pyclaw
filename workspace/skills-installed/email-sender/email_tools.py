#!/usr/bin/env python3
"""
Email Sender Tools
==================

邮件发送工具集，提供：
- send_email: 发送邮件
- configure_email: 配置 SMTP 账户
- test_email: 测试邮件发送
"""

import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Dict, List, Optional, Any


# 配置存储路径
CONFIG_DIR = Path.home() / ".openclaw" / "skills" / "email-sender"
CONFIG_FILE = CONFIG_DIR / "config.json"

# 默认 SMTP 配置
SMTP_PRESETS = {
    "qq": {
        "smtp_server": "smtp.qq.com",
        "smtp_port": 587,
        "use_tls": True,
    },
    "gmail": {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "use_tls": True,
    },
    "163": {
        "smtp_server": "smtp.163.com",
        "smtp_port": 587,
        "use_tls": True,
    },
    "company": {
        "smtp_server": "",  # 需要手动填写
        "smtp_port": 587,
        "use_tls": True,
    },
}


def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"⚠️  加载配置失败：{e}")
    
    # 返回默认配置
    return {
        "default_provider": "qq",
        "accounts": {},
    }


def save_config(config: Dict[str, Any]):
    """保存配置文件"""
    # 确保目录存在
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    # 保存配置
    CONFIG_FILE.write_text(
        json.dumps(config, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    
    # 设置文件权限（仅所有者可读写）
    os.chmod(CONFIG_FILE, 0o600)
    
    print(f"✓ 配置已保存：{CONFIG_FILE}")


def configure_email(
    provider: str = "qq",
    email: str = "",
    password: str = "",
    smtp_server: str = "",
    smtp_port: int = 0,
    use_tls: bool = True,
) -> Dict[str, Any]:
    """
    配置 SMTP 邮箱账户
    
    参数:
        provider: 邮箱服务商（qq/gmail/163/company）
        email: 邮箱地址
        password: 授权码/密码
        smtp_server: SMTP 服务器（可选，自动匹配）
        smtp_port: SMTP 端口（可选，自动匹配）
        use_tls: 是否使用 TLS
    
    返回:
        配置结果
    """
    # 加载现有配置
    config = load_config()
    
    # 验证 provider
    if provider not in SMTP_PRESETS:
        return {
            "success": False,
            "error": f"不支持的邮箱服务商：{provider}",
            "supported": list(SMTP_PRESETS.keys()),
        }
    
    # 验证邮箱格式
    if not email or "@" not in email:
        return {
            "success": False,
            "error": "无效的邮箱地址",
        }
    
    # 验证密码
    if not password:
        return {
            "success": False,
            "error": "密码/授权码不能为空",
        }
    
    # 获取默认 SMTP 配置
    default_config = SMTP_PRESETS[provider]
    
    # 构建账户配置
    account_config = {
        "email": email,
        "password": password,
        "smtp_server": smtp_server or default_config["smtp_server"],
        "smtp_port": smtp_port or default_config["smtp_port"],
        "use_tls": use_tls,
    }
    
    # 保存配置
    config["accounts"][provider] = account_config
    config["default_provider"] = provider
    save_config(config)
    
    return {
        "success": True,
        "message": f"✓ 邮箱配置成功：{email}",
        "provider": provider,
        "email": email,
    }


def send_email(
    to: str,
    subject: str,
    body: str,
    html: bool = False,
    attachment: str = "",
    cc: str = "",
    bcc: str = "",
    provider: str = "",
) -> Dict[str, Any]:
    """
    发送邮件
    
    参数:
        to: 收件人邮箱（多个用逗号分隔）
        subject: 邮件主题
        body: 邮件正文
        html: 是否为 HTML 格式
        attachment: 附件路径（多个用逗号分隔）
        cc: 抄送邮箱（多个用逗号分隔）
        bcc: 密送邮箱（多个用逗号分隔）
        provider: 使用的邮箱服务商（可选，默认配置的）
    
    返回:
        发送结果
    """
    # 加载配置
    config = load_config()
    
    # 确定使用的 provider
    if not provider:
        provider = config.get("default_provider", "qq")
    
    # 获取账户配置
    accounts = config.get("accounts", {})
    if provider not in accounts:
        return {
            "success": False,
            "error": f"未配置 {provider} 邮箱，请先运行 configure_email",
        }
    
    account = accounts[provider]
    
    # 解析收件人
    to_emails = [e.strip() for e in to.split(",") if e.strip()]
    if not to_emails:
        return {
            "success": False,
            "error": "收件人不能为空",
        }
    
    # 解析抄送
    cc_emails = [e.strip() for e in cc.split(",") if e.strip()] if cc else []
    
    # 解析密送
    bcc_emails = [e.strip() for e in bcc.split(",") if e.strip()] if bcc else []
    
    # 解析附件
    attachments = [a.strip() for a in attachment.split(",") if a.strip()] if attachment else []
    
    # 创建邮件
    msg = MIMEMultipart()
    from_email = account["email"]
    msg["From"] = from_email
    msg["To"] = ", ".join(to_emails)
    msg["Subject"] = subject
    
    if cc_emails:
        msg["Cc"] = ", ".join(cc_emails)
    
    # 添加正文
    content_type = "html" if html else "plain"
    msg.attach(MIMEText(body, content_type, "utf-8"))
    
    # 添加附件
    for file_path in attachments:
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"附件不存在：{file_path}",
            }
        
        try:
            with open(file_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
                encoders.encode_base64(part)
                
                filename = os.path.basename(file_path)
                part.add_header(
                    "Content-Disposition",
                    f'attachment; filename="{filename}"'
                )
                msg.attach(part)
        except Exception as e:
            return {
                "success": False,
                "error": f"附件添加失败：{file_path} - {e}",
            }
    
    # 合并收件人列表
    all_recipients = to_emails[:] + cc_emails + bcc_emails
    
    try:
        # 连接 SMTP 服务器
        smtp_server = account["smtp_server"]
        smtp_port = account["smtp_port"]
        use_tls = account.get("use_tls", True)
        
        if use_tls:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        
        # 登录
        server.login(account["email"], account["password"])
        
        # 发送邮件
        server.send_message(msg, to_addrs=all_recipients)
        server.quit()
        
        return {
            "success": True,
            "message": f"✓ 邮件已发送到：{', '.join(to_emails)}",
            "to": to_emails,
            "cc": cc_emails if cc_emails else None,
            "attachments": len(attachments),
        }
    
    except smtplib.SMTPAuthenticationError:
        return {
            "success": False,
            "error": "SMTP 认证失败，请检查邮箱账号和授权码",
        }
    except smtplib.SMTPConnectError:
        return {
            "success": False,
            "error": f"无法连接到 SMTP 服务器：{smtp_server}:{smtp_port}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"发送失败：{e}",
        }


def test_email(to: str = "") -> Dict[str, Any]:
    """
    测试邮件发送
    
    参数:
        to: 收件人邮箱（可选，默认发送到配置的邮箱）
    
    返回:
        测试结果
    """
    # 加载配置
    config = load_config()
    provider = config.get("default_provider", "qq")
    accounts = config.get("accounts", {})
    
    if provider not in accounts:
        return {
            "success": False,
            "error": f"未配置 {provider} 邮箱",
        }
    
    account = accounts[provider]
    
    # 确定测试收件人
    if not to:
        to = account["email"]  # 发送到自己
    
    # 发送测试邮件
    subject = "📧 PyClaw Email Test"
    body = """
<h2>邮件测试成功！✅</h2>

<p>这是一封测试邮件，用于验证 SMTP 配置是否正确。</p>

<h3>配置信息：</h3>
<ul>
  <li>发件人：{from_email}</li>
  <li>收件人：{to_email}</li>
  <li>时间：{time}</li>
</ul>

<p>如果收到这封邮件，说明配置正确！🎉</p>
""".format(
        from_email=account["email"],
        to_email=to,
        time=__import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    
    return send_email(
        to=to,
        subject=subject,
        body=body,
        html=True,
    )


def list_accounts() -> Dict[str, Any]:
    """
    列出已配置的邮箱账户
    
    返回:
        账户列表
    """
    config = load_config()
    accounts = config.get("accounts", {})
    
    # 隐藏密码，只显示邮箱
    masked_accounts = {}
    for provider, account in accounts.items():
        masked_accounts[provider] = {
            "email": account["email"],
            "smtp_server": account["smtp_server"],
            "smtp_port": account["smtp_port"],
        }
    
    return {
        "success": True,
        "default_provider": config.get("default_provider"),
        "accounts": masked_accounts,
    }


def delete_account(provider: str) -> Dict[str, Any]:
    """
    删除已配置的邮箱账户
    
    参数:
        provider: 邮箱服务商
    
    返回:
        删除结果
    """
    config = load_config()
    
    if provider not in config.get("accounts", {}):
        return {
            "success": False,
            "error": f"未找到 {provider} 邮箱配置",
        }
    
    del config["accounts"][provider]
    save_config(config)
    
    return {
        "success": True,
        "message": f"✓ 已删除 {provider} 邮箱配置",
    }


# CLI 入口
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法：python email_tools.py <command> [args]")
        print("命令：")
        print("  configure  - 配置邮箱")
        print("  send       - 发送邮件")
        print("  test       - 测试邮件")
        print("  list       - 列出账户")
        print("  delete     - 删除账户")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "configure":
        # python email_tools.py configure qq email@example.com password
        if len(sys.argv) < 5:
            print("用法：python email_tools.py configure <provider> <email> <password>")
            sys.exit(1)
        result = configure_email(sys.argv[2], sys.argv[3], sys.argv[4])
    
    elif command == "send":
        # python email_tools.py send to subject body [html] [attachment]
        if len(sys.argv) < 5:
            print("用法：python email_tools.py send <to> <subject> <body> [html] [attachment]")
            sys.exit(1)
        html = sys.argv[5].lower() == "true" if len(sys.argv) > 5 else False
        attachment = sys.argv[6] if len(sys.argv) > 6 else ""
        result = send_email(sys.argv[2], sys.argv[3], sys.argv[4], html, attachment)
    
    elif command == "test":
        to = sys.argv[2] if len(sys.argv) > 2 else ""
        result = test_email(to)
    
    elif command == "list":
        result = list_accounts()
    
    elif command == "delete":
        if len(sys.argv) < 3:
            print("用法：python email_tools.py delete <provider>")
            sys.exit(1)
        result = delete_account(sys.argv[2])
    
    else:
        print(f"未知命令：{command}")
        sys.exit(1)
    
    # 输出结果
    print(json.dumps(result, indent=2, ensure_ascii=False))
