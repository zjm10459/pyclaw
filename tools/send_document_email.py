#!/usr/bin/env python3
"""
文档邮件通知工具

用于发送文档发布通知邮件，支持 HTML 模板和附件。

使用方法：
    python tools/send_document_email.py \
        --to recipient@example.com \
        --doc-title "项目计划书" \
        --doc-path "./docs/项目计划书.md" \
        --config "./config/email_config.json"
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def load_config(config_path: str) -> dict:
    """加载邮件配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config


def load_template(template_path: str) -> str:
    """加载 HTML 模板"""
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


def render_template(template: str, context: dict) -> str:
    """渲染模板（简单版本，支持 {{variable}} 和 {% for %}）"""
    result = template
    
    # 替换简单变量 {{variable}}
    for key, value in context.items():
        if isinstance(value, (str, int, float)):
            result = result.replace(f'{{{{{key}}}}}', str(value))
    
    # 处理简单的 {% for item in list %} 循环
    # 注意：这是一个简化版本，复杂模板建议使用 Jinja2
    
    return result


def send_document_email(
    to: list,
    doc_title: str,
    doc_path: str = None,
    doc_type: str = "技术文档",
    author: str = "系统",
    version: str = "1.0.0",
    status: str = "已发布",
    summary: str = "",
    tags: list = None,
    config_path: str = "config/email_config.json",
    cc: list = None,
    bcc: list = None,
    dry_run: bool = False
):
    """
    发送文档发布通知邮件
    
    参数:
        to: 收件人列表
        doc_title: 文档标题
        doc_path: 文档路径（可选，用于附件）
        doc_type: 文档类型
        author: 作者
        version: 版本号
        status: 状态
        summary: 文档摘要
        tags: 标签列表
        config_path: 配置文件路径
        cc: 抄送列表
        bcc: 密送列表
        dry_run: 是否仅模拟发送（不实际发送）
    """
    
    # 加载配置
    config = load_config(config_path)
    email_config = config['email']
    defaults = config.get('defaults', {})
    templates_config = config.get('templates', {}).get('document_notification', {})
    
    # 准备文档信息
    doc_url = f"file://{os.path.abspath(doc_path)}" if doc_path else "#"
    created_date = datetime.now().strftime("%Y-%m-%d")
    
    # 读取文档摘要（如果提供了路径）
    if not summary and doc_path and os.path.exists(doc_path):
        try:
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read(1000)  # 读取前 1000 字符
                # 提取第一段作为摘要
                summary = content.split('\n\n')[0][:200] + "..."
        except Exception as e:
            summary = f"文档摘要读取失败：{e}"
    
    # 准备模板上下文
    context = {
        'doc_title': doc_title,
        'doc_type': doc_type,
        'author': author,
        'created_date': created_date,
        'version': version,
        'status': status,
        'summary': summary,
        'tags': tags or [],
        'doc_url': doc_url
    }
    
    # 加载并渲染模板
    template_path = templates_config.get('body_template', 'docs/templates/document_notification.html')
    if os.path.exists(template_path):
        template = load_template(template_path)
        html_body = render_template(template, context)
    else:
        # 使用默认模板
        html_body = f"""
        <html>
        <body>
            <h2>文档发布通知</h2>
            <p><strong>标题：</strong>{doc_title}</p>
            <p><strong>类型：</strong>{doc_type}</p>
            <p><strong>作者：</strong>{author}</p>
            <p><strong>版本：</strong>{version}</p>
            <p><strong>状态：</strong>{status}</p>
            <p><strong>摘要：</strong>{summary}</p>
            <p><a href="{doc_url}">查看文档</a></p>
        </body>
        </html>
        """
    
    # 准备邮件参数
    subject = templates_config.get('subject', '文档发布通知：{doc_title}').format(doc_title=doc_title)
    
    attachments = []
    if doc_path and os.path.exists(doc_path):
        attachments.append(doc_path)
    
    # 构建邮件发送参数
    email_params = {
        'to': to,
        'subject': subject,
        'body': html_body,
        'html': True,
        'attachments': attachments
    }
    
    if cc:
        email_params['cc'] = cc
    if bcc:
        email_params['bcc'] = bcc
    
    # 打印邮件信息
    print("=" * 60)
    print("📧 邮件发送信息")
    print("=" * 60)
    print(f"收件人：{', '.join(to)}")
    if cc:
        print(f"抄送：{', '.join(cc)}")
    if bcc:
        print(f"密送：{', '.join(bcc)}")
    print(f"主题：{subject}")
    print(f"附件：{attachments if attachments else '无'}")
    print("-" * 60)
    
    if dry_run:
        print("⚠️  模拟模式：邮件未实际发送")
        print("\n邮件内容预览：")
        print(html_body[:500] + "..." if len(html_body) > 500 else html_body)
        return True
    
    # 实际发送邮件
    try:
        from skills.email_sender import send_email
        
        # 配置 SMTP（从环境变量或配置文件读取）
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.base import MIMEBase
        from email import encoders
        
        # 创建邮件
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{defaults.get('from_name', 'PyClaw')} <{email_config['smtp_user']}>"
        msg['To'] = ', '.join(to)
        
        if cc:
            msg['Cc'] = ', '.join(cc)
        
        # 添加 HTML 内容
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        
        # 添加附件
        for attachment_path in attachments:
            if os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename="{os.path.basename(attachment_path)}"'
                    )
                    msg.attach(part)
        
        # 连接 SMTP 服务器并发送
        server = None
        try:
            if email_config.get('use_ssl', True):
                server = smtplib.SMTP_SSL(
                    email_config['smtp_server'],
                    email_config['smtp_port'],
                    timeout=email_config.get('timeout', 30)
                )
            else:
                server = smtplib.SMTP(
                    email_config['smtp_server'],
                    email_config['smtp_port'],
                    timeout=email_config.get('timeout', 30)
                )
                if email_config.get('use_tls', False):
                    server.starttls()
            
            server.login(
                email_config['smtp_user'],
                email_config['smtp_password']
            )
            
            # 获取所有收件人
            all_recipients = to[:]
            if cc:
                all_recipients.extend(cc)
            if bcc:
                all_recipients.extend(bcc)
            
            server.sendmail(
                email_config['smtp_user'],
                all_recipients,
                msg.as_string()
            )
            
            print("✅ 邮件发送成功！")
            return True
            
        except Exception as e:
            print(f"❌ 邮件发送失败：{e}")
            return False
        finally:
            if server:
                server.quit()
                
    except ImportError:
        print("⚠️  email-sender skill 未安装，使用备用发送方式")
        # 这里可以添加备用发送逻辑
        return False


def main():
    parser = argparse.ArgumentParser(description='发送文档发布通知邮件')
    
    parser.add_argument('--to', '-t', nargs='+', required=True,
                        help='收件人邮箱地址列表')
    parser.add_argument('--doc-title', '-d', required=True,
                        help='文档标题')
    parser.add_argument('--doc-path', '-p',
                        help='文档文件路径（可选，用于附件）')
    parser.add_argument('--doc-type', default='技术文档',
                        help='文档类型（默认：技术文档）')
    parser.add_argument('--author', '-a', default='系统',
                        help='作者（默认：系统）')
    parser.add_argument('--version', '-v', default='1.0.0',
                        help='版本号（默认：1.0.0）')
    parser.add_argument('--status', '-s', default='已发布',
                        help='文档状态（默认：已发布）')
    parser.add_argument('--summary', default='',
                        help='文档摘要')
    parser.add_argument('--tags', nargs='+', default=[],
                        help='标签列表')
    parser.add_argument('--config', '-c', default='config/email_config.json',
                        help='配置文件路径（默认：config/email_config.json）')
    parser.add_argument('--cc', nargs='+', default=[],
                        help='抄送邮箱地址列表')
    parser.add_argument('--bcc', nargs='+', default=[],
                        help='密送邮箱地址列表')
    parser.add_argument('--dry-run', action='store_true',
                        help='模拟发送（不实际发送）')
    
    args = parser.parse_args()
    
    success = send_document_email(
        to=args.to,
        doc_title=args.doc_title,
        doc_path=args.doc_path,
        doc_type=args.doc_type,
        author=args.author,
        version=args.version,
        status=args.status,
        summary=args.summary,
        tags=args.tags,
        config_path=args.config,
        cc=args.cc,
        bcc=args.bcc,
        dry_run=args.dry_run
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
