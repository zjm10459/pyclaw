#!/usr/bin/env python3
"""
Email Skill for OpenClaw
========================

OpenClaw Skill 包装器，将邮件工具集成到 OpenClaw 工具系统。

使用方式：
    在 OpenClaw 中调用：
    - send_email(to="...", subject="...", body="...")
    - configure_email(provider="qq", email="...", password="...")
    - test_email(to="...")
"""

import sys
import json
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from email_tools import (
    send_email,
    configure_email,
    test_email,
    list_accounts,
    delete_account,
)


def tool_send_email(
    to: str,
    subject: str,
    body: str,
    html: bool = False,
    attachment: str = "",
    cc: str = "",
    bcc: str = "",
    provider: str = "",
) -> dict:
    """
    发送邮件
    
    参数:
        to: 收件人邮箱，多个用逗号分隔
        subject: 邮件主题
        body: 邮件正文
        html: 是否为 HTML 格式
        attachment: 附件路径，多个用逗号分隔
        cc: 抄送邮箱
        bcc: 密送邮箱
        provider: 邮箱服务商
    
    返回:
        发送结果
    """
    result = send_email(
        to=to,
        subject=subject,
        body=body,
        html=html,
        attachment=attachment,
        cc=cc,
        bcc=bcc,
        provider=provider,
    )
    return result


def tool_configure_email(
    provider: str = "qq",
    email: str = "",
    password: str = "",
    smtp_server: str = "",
    smtp_port: int = 0,
    use_tls: bool = True,
) -> dict:
    """
    配置 SMTP 邮箱账户
    
    参数:
        provider: 邮箱服务商（qq/gmail/163/company）
        email: 邮箱地址
        password: 授权码/密码
        smtp_server: SMTP 服务器
        smtp_port: SMTP 端口
        use_tls: 是否使用 TLS
    
    返回:
        配置结果
    """
    result = configure_email(
        provider=provider,
        email=email,
        password=password,
        smtp_server=smtp_server,
        smtp_port=smtp_port,
        use_tls=use_tls,
    )
    return result


def tool_test_email(to: str = "") -> dict:
    """
    测试邮件发送
    
    参数:
        to: 收件人邮箱（可选）
    
    返回:
        测试结果
    """
    result = test_email(to=to)
    return result


def tool_list_email_accounts() -> dict:
    """
    列出已配置的邮箱账户
    
    返回:
        账户列表
    """
    result = list_accounts()
    return result


def tool_delete_email_account(provider: str) -> dict:
    """
    删除已配置的邮箱账户
    
    参数:
        provider: 邮箱服务商
    
    返回:
        删除结果
    """
    result = delete_account(provider)
    return result


# 导出所有工具函数
__all__ = [
    "tool_send_email",
    "tool_configure_email",
    "tool_test_email",
    "tool_list_email_accounts",
    "tool_delete_email_account",
]


# CLI 测试入口
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Email Skill for OpenClaw")
        print("可用工具:")
        print("  - send_email")
        print("  - configure_email")
        print("  - test_email")
        print("  - list_email_accounts")
        print("  - delete_email_account")
        sys.exit(0)
    
    tool_name = sys.argv[1]
    
    # 简单测试
    if tool_name == "test":
        print("测试 Email Skill...")
        result = tool_list_email_accounts()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"未知工具：{tool_name}")
        sys.exit(1)
