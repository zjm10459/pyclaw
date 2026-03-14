#!/usr/bin/env python3
"""
Email Sender Script
===================

通过命令行发送邮件，支持附件、HTML、抄送等功能。

使用方式:
    python send_email.py send --to user@example.com --subject "主题" --body "正文"
    python send_email.py send --to user@example.com --subject "主题" --body "正文" --html
    python send_email.py send --to user@example.com --subject "主题" --body "正文" --attachment /path/to/file.pdf
    python send_email.py configure --provider qq --email 1045935055@qq.com --password 授权码
    python send_email.py test --to user@example.com
    python send_email.py list
    python send_email.py delete --provider qq
"""

import argparse
import json
import os
import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from datetime import datetime
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
            print(f"⚠️  加载配置失败：{e}", file=sys.stderr)
    
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


def configure_email_cmd(
    provider: str,
    email: str,
    password: str,
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


def send_email_cmd(
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
            "error": f"未配置 {provider} 邮箱，请先运行 configure 命令",
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


def test_email_cmd(to: str = "") -> Dict[str, Any]:
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
    body = f"""
<h2>邮件测试成功！✅</h2>

<p>这是一封测试邮件，用于验证 SMTP 配置是否正确。</p>

<h3>配置信息：</h3>
<ul>
  <li>发件人：{account["email"]}</li>
  <li>收件人：{to}</li>
  <li>时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</li>
</ul>

<p>如果收到这封邮件，说明配置正确！🎉</p>
"""
    
    return send_email_cmd(
        to=to,
        subject=subject,
        body=body,
        html=True,
    )


def list_accounts_cmd() -> Dict[str, Any]:
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


def delete_account_cmd(provider: str) -> Dict[str, Any]:
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


def main():
    """主函数 - 命令行入口"""
    parser = argparse.ArgumentParser(
        description="Email Sender - 通过 SMTP 发送邮件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python send_email.py configure --provider qq --email 1045935055@qq.com --password 授权码
  python send_email.py send --to user@example.com --subject "主题" --body "正文"
  python send_email.py send --to user@example.com --subject "主题" --body "正文" --html
  python send_email.py send --to user@example.com --subject "主题" --body "正文" --attachment /path/to/file.pdf
  python send_email.py test --to user@example.com
  python send_email.py list
  python send_email.py delete --provider qq
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # ========== configure 命令 ==========
    configure_parser = subparsers.add_parser("configure", help="配置邮箱账户")
    configure_parser.add_argument("--provider", "-p", required=True, 
                                  choices=["qq", "gmail", "163", "company"],
                                  help="邮箱服务商")
    configure_parser.add_argument("--email", "-e", required=True, help="邮箱地址")
    configure_parser.add_argument("--password", "-P", required=True, help="授权码/密码")
    configure_parser.add_argument("--smtp-server", "-s", default="", help="SMTP 服务器（可选）")
    configure_parser.add_argument("--smtp-port", "-S", type=int, default=0, help="SMTP 端口（可选）")
    configure_parser.add_argument("--no-tls", action="store_true", help="不使用 TLS")
    
    # ========== send 命令 ==========
    send_parser = subparsers.add_parser("send", help="发送邮件")
    send_parser.add_argument("--to", "-t", required=True, help="收件人邮箱（多个用逗号分隔）")
    send_parser.add_argument("--subject", "-subj", required=True, help="邮件主题")
    send_parser.add_argument("--body", "-b", required=True, help="邮件正文")
    send_parser.add_argument("--html", action="store_true", help="是否为 HTML 格式")
    send_parser.add_argument("--attachment", "-a", default="", help="附件路径（多个用逗号分隔）")
    send_parser.add_argument("--cc", default="", help="抄送邮箱（多个用逗号分隔）")
    send_parser.add_argument("--bcc", default="", help="密送邮箱（多个用逗号分隔）")
    send_parser.add_argument("--provider", "-p", default="", help="使用的邮箱服务商（可选）")
    
    # ========== test 命令 ==========
    test_parser = subparsers.add_parser("test", help="测试邮件发送")
    test_parser.add_argument("--to", "-t", default="", help="收件人邮箱（可选，默认发送到配置的邮箱）")
    
    # ========== list 命令 ==========
    subparsers.add_parser("list", help="列出已配置的邮箱账户")
    
    # ========== delete 命令 ==========
    delete_parser = subparsers.add_parser("delete", help="删除邮箱账户")
    delete_parser.add_argument("--provider", "-p", required=True, 
                               choices=["qq", "gmail", "163", "company"],
                               help="邮箱服务商")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # 执行对应命令
    if args.command == "configure":
        result = configure_email_cmd(
            provider=args.provider,
            email=args.email,
            password=args.password,
            smtp_server=args.smtp_server or "",
            smtp_port=args.smtp_port or 0,
            use_tls=not args.no_tls,
        )
    
    elif args.command == "send":
        result = send_email_cmd(
            to=args.to,
            subject=args.subject,
            body=args.body,
            html=args.html,
            attachment=args.attachment,
            cc=args.cc,
            bcc=args.bcc,
            provider=args.provider,
        )
    
    elif args.command == "test":
        result = test_email_cmd(to=args.to)
    
    elif args.command == "list":
        result = list_accounts_cmd()
    
    elif args.command == "delete":
        result = delete_account_cmd(provider=args.provider)
    
    else:
        parser.print_help()
        sys.exit(1)
    
    # 输出结果（JSON 格式，便于 AI 解析）
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 根据成功/失败设置退出码
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
