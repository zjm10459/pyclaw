#!/usr/bin/env python3
"""
邮件发送工作流自动化脚本

提供多种预定义的邮件发送场景：
1. 文档发布通知
2. 周报自动发送
3. 项目更新通知
4. 告警邮件发送

使用方法：
    python tools/email_workflow.py <workflow_name> [options]
    
示例：
    python tools/email_workflow.py doc-notify --doc "./docs/项目计划.md" --to team@company.com
    python tools/email_workflow.py weekly-report --week "2026-W11" --to manager@company.com
    python tools/email_workflow.py alert --title "系统异常" --message "服务不可用" --to oncall@company.com
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class EmailWorkflow:
    """邮件工作流管理器"""
    
    def __init__(self, config_path: str = "config/email_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """加载配置文件"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def send_doc_notification(
        self,
        doc_path: str,
        to: List[str],
        doc_type: str = "技术文档",
        author: str = None,
        cc: List[str] = None,
        dry_run: bool = False
    ):
        """
        工作流 1: 文档发布通知
        
        自动提取文档信息并发送通知邮件
        """
        from tools.send_document_email import send_document_email
        
        # 提取文档信息
        doc_title = Path(doc_path).stem
        if not author:
            author = os.getenv("USER", "系统")
        
        # 尝试从文档中提取元信息
        metadata = self._extract_doc_metadata(doc_path)
        
        print(f"📄 准备发送文档通知：{doc_title}")
        print(f"   路径：{doc_path}")
        print(f"   收件人：{', '.join(to)}")
        
        return send_document_email(
            to=to,
            doc_title=metadata.get('title', doc_title),
            doc_path=doc_path,
            doc_type=doc_type,
            author=metadata.get('author', author),
            version=metadata.get('version', '1.0.0'),
            status=metadata.get('status', '已发布'),
            summary=metadata.get('description', ''),
            tags=metadata.get('tags', []),
            config_path=self.config_path,
            cc=cc,
            dry_run=dry_run
        )
    
    def send_weekly_report(
        self,
        week: str,
        content: str,
        to: List[str],
        author: str = None,
        completed_items: List[str] = None,
        planned_items: List[str] = None,
        cc: List[str] = None,
        dry_run: bool = False
    ):
        """
        工作流 2: 周报自动发送
        
        发送格式化的周报邮件
        """
        if not author:
            author = os.getenv("USER", "系统")
        
        # 生成 HTML 邮件内容
        html_content = self._generate_weekly_report_html(
            week=week,
            author=author,
            completed=completed_items or [],
            planned=planned_items or [],
            notes=content
        )
        
        subject = f"周报 - {week}"
        
        print(f"📊 准备发送周报：{week}")
        print(f"   作者：{author}")
        print(f"   收件人：{', '.join(to)}")
        
        return self._send_email(
            to=to,
            subject=subject,
            body=html_content,
            html=True,
            cc=cc,
            dry_run=dry_run
        )
    
    def send_project_update(
        self,
        project_name: str,
        update_type: str,
        content: str,
        to: List[str],
        milestone: str = None,
        progress: float = None,
        cc: List[str] = None,
        dry_run: bool = False
    ):
        """
        工作流 3: 项目更新通知
        
        发送项目进度更新邮件
        """
        # 生成 HTML 邮件内容
        html_content = self._generate_project_update_html(
            project_name=project_name,
            update_type=update_type,
            content=content,
            milestone=milestone,
            progress=progress
        )
        
        subject = f"【项目更新】{project_name} - {update_type}"
        
        print(f"📈 准备发送项目更新：{project_name}")
        print(f"   类型：{update_type}")
        print(f"   收件人：{', '.join(to)}")
        
        return self._send_email(
            to=to,
            subject=subject,
            body=html_content,
            html=True,
            cc=cc,
            dry_run=dry_run
        )
    
    def send_alert(
        self,
        title: str,
        message: str,
        to: List[str],
        level: str = "warning",
        cc: List[str] = None,
        dry_run: bool = False
    ):
        """
        工作流 4: 告警邮件发送
        
        发送紧急告警邮件
        """
        # 根据级别设置样式
        level_colors = {
            'info': '#17a2b8',
            'warning': '#ffc107',
            'error': '#dc3545',
            'critical': '#721c24'
        }
        
        level_icons = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'critical': '🚨'
        }
        
        color = level_colors.get(level, '#ffc107')
        icon = level_icons.get(level, '⚠️')
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <div style="background: {color}; color: white; padding: 20px; border-radius: 5px;">
                <h1 style="margin: 0;">{icon} {title}</h1>
            </div>
            <div style="padding: 20px; background: #f9f9f9;">
                <p style="font-size: 16px;">{message.replace(chr(10), '<br>')}</p>
                <p style="color: #666; font-size: 12px; margin-top: 30px;">
                    发送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                    告警级别：{level.upper()}
                </p>
            </div>
        </body>
        </html>
        """
        
        subject = f"【告警】{title}"
        
        print(f"🚨 准备发送告警：{title}")
        print(f"   级别：{level}")
        print(f"   收件人：{', '.join(to)}")
        
        return self._send_email(
            to=to,
            subject=subject,
            body=html_content,
            html=True,
            cc=cc,
            dry_run=dry_run
        )
    
    def _extract_doc_metadata(self, doc_path: str) -> dict:
        """从 Markdown 文档中提取元信息"""
        metadata = {}
        
        if not os.path.exists(doc_path):
            return metadata
        
        try:
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read(2000)  # 读取前 2000 字符
                
                # 提取标题
                lines = content.split('\n')
                for line in lines:
                    if line.startswith('# '):
                        metadata['title'] = line[2:].strip()
                        break
                
                # 提取元信息块
                if content.startswith('---\n'):
                    end_index = content.find('\n---\n', 4)
                    if end_index > 0:
                        yaml_block = content[4:end_index]
                        for line in yaml_block.split('\n'):
                            if ':' in line:
                                key, value = line.split(':', 1)
                                metadata[key.strip()] = value.strip()
                
                # 提取描述（第一个段落）
                for line in lines:
                    if line.strip() and not line.startswith('#') and not line.startswith('>'):
                        if 'description' not in metadata:
                            metadata['description'] = line[:200]
                        break
                
                # 提取标签
                if 'tags' in content.lower():
                    import re
                    tags_match = re.search(r'标签 [::]\s*(.+)', content)
                    if tags_match:
                        metadata['tags'] = [t.strip() for t in tags_match.group(1).split(',')]
                
        except Exception as e:
            print(f"⚠️  提取元信息失败：{e}")
        
        return metadata
    
    def _generate_weekly_report_html(
        self,
        week: str,
        author: str,
        completed: List[str],
        planned: List[str],
        notes: str = ""
    ) -> str:
        """生成周报 HTML"""
        completed_html = ''.join([f"<li>{item}</li>" for item in completed])
        planned_html = ''.join([f"<li>{item}</li>" for item in planned])
        
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; }}
                .section {{ margin: 20px 0; }}
                .section h3 {{ color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
                .content {{ background: #f9f9f9; padding: 30px; }}
                .footer {{ background: #f0f0f0; padding: 20px; text-align: center; font-size: 12px; color: #666; border-radius: 0 0 10px 10px; }}
                ul {{ padding-left: 20px; }}
                li {{ margin: 8px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 周报</h1>
                <p>周期：{week} | 作者：{author}</p>
            </div>
            <div class="content">
                <div class="section">
                    <h3>✅ 本周完成</h3>
                    <ul>{completed_html}</ul>
                </div>
                <div class="section">
                    <h3>📅 下周计划</h3>
                    <ul>{planned_html}</ul>
                </div>
                {f'<div class="section"><h3>📝 备注</h3><p>{notes}</p></div>' if notes else ''}
            </div>
            <div class="footer">
                <p>发送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """
    
    def _generate_project_update_html(
        self,
        project_name: str,
        update_type: str,
        content: str,
        milestone: str = None,
        progress: float = None
    ) -> str:
        """生成项目更新 HTML"""
        progress_bar = ""
        if progress is not None:
            progress_bar = f"""
            <div style="margin: 20px 0;">
                <p>项目进度：{progress}%</p>
                <div style="background: #e0e0e0; border-radius: 10px; overflow: hidden;">
                    <div style="width: {progress}%; background: linear-gradient(90deg, #667eea, #764ba2); height: 20px;"></div>
                </div>
            </div>
            """
        
        milestone_html = f"<p><strong>当前里程碑：</strong>{milestone}</p>" if milestone else ""
        
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; }}
                .badge {{ display: inline-block; padding: 5px 15px; background: rgba(255,255,255,0.2); border-radius: 20px; font-size: 14px; }}
                .content {{ background: #f9f9f9; padding: 30px; margin-top: 20px; border-radius: 10px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📈 {project_name}</h1>
                <span class="badge">{update_type}</span>
            </div>
            <div class="content">
                {milestone_html}
                {progress_bar}
                <div style="margin-top: 20px;">
                    {content.replace(chr(10), '<br>')}
                </div>
            </div>
        </body>
        </html>
        """
    
    def _send_email(
        self,
        to: List[str],
        subject: str,
        body: str,
        html: bool = True,
        cc: List[str] = None,
        bcc: List[str] = None,
        attachments: List[str] = None,
        dry_run: bool = False
    ) -> bool:
        """通用邮件发送方法"""
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.base import MIMEBase
        from email import encoders
        
        email_config = self.config.get('email', {})
        defaults = self.config.get('defaults', {})
        
        if dry_run:
            print("=" * 60)
            print("📧 邮件预览（模拟模式）")
            print("=" * 60)
            print(f"收件人：{', '.join(to)}")
            if cc:
                print(f"抄送：{', '.join(cc)}")
            print(f"主题：{subject}")
            print("-" * 60)
            print(body[:500] + "..." if len(body) > 500 else body)
            print("=" * 60)
            print("⚠️  邮件未实际发送")
            return True
        
        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{defaults.get('from_name', 'PyClaw')} <{email_config.get('smtp_user', 'noreply')}>"
            msg['To'] = ', '.join(to)
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            
            # 添加内容
            msg.attach(MIMEText(body, 'html' if html else 'plain', 'utf-8'))
            
            # 添加附件
            if attachments:
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
            
            # 发送
            server = None
            try:
                if email_config.get('use_ssl', True):
                    server = smtplib.SMTP_SSL(
                        email_config.get('smtp_server', 'smtp.qq.com'),
                        email_config.get('smtp_port', 465),
                        timeout=email_config.get('timeout', 30)
                    )
                else:
                    server = smtplib.SMTP(
                        email_config.get('smtp_server', 'smtp.qq.com'),
                        email_config.get('smtp_port', 587),
                        timeout=email_config.get('timeout', 30)
                    )
                    if email_config.get('use_tls', False):
                        server.starttls()
                
                server.login(
                    email_config.get('smtp_user', ''),
                    email_config.get('smtp_password', '')
                )
                
                all_recipients = to[:]
                if cc:
                    all_recipients.extend(cc)
                if bcc:
                    all_recipients.extend(bcc)
                
                server.sendmail(
                    email_config.get('smtp_user', ''),
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
                    
        except Exception as e:
            print(f"❌ 错误：{e}")
            return False


def main():
    parser = argparse.ArgumentParser(description='邮件发送工作流自动化')
    parser.add_argument('workflow', choices=['doc-notify', 'weekly-report', 'project-update', 'alert'],
                        help='工作流类型')
    parser.add_argument('--config', '-c', default='config/email_config.json',
                        help='配置文件路径')
    parser.add_argument('--to', '-t', nargs='+', required=True,
                        help='收件人邮箱列表')
    parser.add_argument('--cc', nargs='+', default=[],
                        help='抄送邮箱列表')
    parser.add_argument('--dry-run', action='store_true',
                        help='模拟发送')
    
    # 文档通知参数
    parser.add_argument('--doc', '-d',
                        help='文档路径（doc-notify 使用）')
    parser.add_argument('--doc-type', default='技术文档',
                        help='文档类型（doc-notify 使用）')
    
    # 周报参数
    parser.add_argument('--week', '-w',
                        help='周报周期（weekly-report 使用）')
    parser.add_argument('--content', default='',
                        help='周报内容（weekly-report 使用）')
    parser.add_argument('--completed', nargs='+', default=[],
                        help='已完成事项（weekly-report 使用）')
    parser.add_argument('--planned', nargs='+', default=[],
                        help='计划事项（weekly-report 使用）')
    
    # 项目更新参数
    parser.add_argument('--project', '-p',
                        help='项目名称（project-update 使用）')
    parser.add_argument('--update-type', '-u', default='进度更新',
                        help='更新类型（project-update 使用）')
    parser.add_argument('--milestone', '-m',
                        help='当前里程碑（project-update 使用）')
    parser.add_argument('--progress', type=float,
                        help='项目进度百分比（project-update 使用）')
    
    # 告警参数
    parser.add_argument('--title',
                        help='告警标题（alert 使用）')
    parser.add_argument('--message',
                        help='告警内容（alert 使用）')
    parser.add_argument('--level', default='warning',
                        choices=['info', 'warning', 'error', 'critical'],
                        help='告警级别（alert 使用）')
    
    args = parser.parse_args()
    
    workflow = EmailWorkflow(config_path=args.config)
    
    if args.workflow == 'doc-notify':
        if not args.doc:
            print("❌ 错误：--doc 参数为必需")
            sys.exit(1)
        success = workflow.send_doc_notification(
            doc_path=args.doc,
            to=args.to,
            doc_type=args.doc_type,
            cc=args.cc,
            dry_run=args.dry_run
        )
    
    elif args.workflow == 'weekly-report':
        if not args.week:
            print("❌ 错误：--week 参数为必需")
            sys.exit(1)
        success = workflow.send_weekly_report(
            week=args.week,
            content=args.content,
            to=args.to,
            completed_items=args.completed,
            planned_items=args.planned,
            cc=args.cc,
            dry_run=args.dry_run
        )
    
    elif args.workflow == 'project-update':
        if not args.project:
            print("❌ 错误：--project 参数为必需")
            sys.exit(1)
        success = workflow.send_project_update(
            project_name=args.project,
            update_type=args.update_type,
            content=args.content,
            to=args.to,
            milestone=args.milestone,
            progress=args.progress,
            cc=args.cc,
            dry_run=args.dry_run
        )
    
    elif args.workflow == 'alert':
        if not args.title or not args.message:
            print("❌ 错误：--title 和 --message 参数为必需")
            sys.exit(1)
        success = workflow.send_alert(
            title=args.title,
            message=args.message,
            to=args.to,
            level=args.level,
            cc=args.cc,
            dry_run=args.dry_run
        )
    
    else:
        print(f"❌ 未知的工作流：{args.workflow}")
        sys.exit(1)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
