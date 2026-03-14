#!/usr/bin/env python3
"""
聊天记录自动保存工具
====================

在对话结束时自动保存当天的聊天记录。

功能：
- JSON 格式保存完整记录
- Markdown 格式保存摘要
- 按日期组织文件
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger("pyclaw.chat_recorder")


def generate_detailed_summary(messages: List[Dict[str, Any]]) -> str:
    """
    自动生成详细摘要
    
    包含：
    - 用户主要意图
    - 使用的工具
    - 工具参数
    - 工具结果
    - AI 回复要点
    
    参数:
        messages: 消息列表
    
    返回:
        详细摘要字符串
    """
    if not messages:
        return "空对话"
    
    # 分类消息
    user_msgs = [m for m in messages if m.get("role") in ["human", "user"]]
    ai_msgs = [m for m in messages if m.get("role") in ["ai", "assistant"]]
    tool_msgs = [m for m in messages if m.get("role") == "tool"]
    
    # 1. 提取用户意图
    user_intent = ""
    if user_msgs:
        user_intent = user_msgs[0].get("content", "")[:80]
    
    # 2. 检测工具调用
    tool_info = []
    tool_queries = []
    for msg in ai_msgs:
        if msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                tool_name = tc.get("name", "unknown")
                tool_args = tc.get("args", {})
                
                tool_info.append(tool_name)
                
                # 提取关键参数
                if "query" in tool_args:
                    query = str(tool_args["query"])[:50]
                    tool_queries.append(f"搜索：{query}")
                elif "url" in tool_args:
                    url = tool_args["url"][:50]
                    tool_queries.append(f"访问：{url}")
    
    # 3. 工具结果摘要
    tool_output = ""
    for msg in tool_msgs:
        content = msg.get("content", "")
        if content:
            if len(content) > 100:
                tool_output = f"获取详细信息 ({len(content)} 字)"
            else:
                tool_output = "获取结果"
            break
    
    # 4. AI 回复要点
    ai_response = ""
    if ai_msgs:
        last_msg = ai_msgs[-1].get("content", "")
        if last_msg:
            # 提取第一句完整的话
            for sep in ["。", "！", "？", "\n"]:
                if sep in last_msg:
                    ai_response = last_msg.split(sep)[0].strip()[:60]
                    break
            if not ai_response:
                ai_response = last_msg[:60]
    
    # 组合摘要
    parts = []
    if user_intent:
        parts.append(f"用户：{user_intent}")
    if tool_info:
        parts.append(f"使用：{', '.join(tool_info)}")
    if tool_queries:
        parts.extend(tool_queries)
    if tool_output:
        parts.append(tool_output)
    if ai_response:
        parts.append(f"回复：{ai_response}")
    
    if parts:
        summary = " | ".join(parts)
        # 限制长度
        if len(summary) > 300:
            summary = summary[:297] + "..."
        return summary
    else:
        return f"对话记录：{len(messages)} 条消息"


def get_chat_record_dir() -> Path:
    """获取聊天记录目录"""
    # PyClaw 项目根目录的 memory_chat 目录
    memory_dir = Path.home() / ".openclaw" / "workspace" / "pyclaw" / "memory_chat"
    
    # 如果不存在，尝试其他路径
    if not memory_dir.exists():
        memory_dir = Path.home() / ".pyclaw" / "workspace" / "pyclaw" / "memory_chat"
    
    if not memory_dir.exists():
        memory_dir = Path.home() / ".pyclaw" / "memory_chat"
    
    memory_dir.mkdir(parents=True, exist_ok=True)
    return memory_dir


def save_chat_record(
    messages: List[Dict[str, Any]],
    session_key: str = "default",
    summary: Optional[str] = None,
    auto_generate_summary: bool = True,
) -> Dict[str, Any]:
    """
    保存聊天记录
    
    参数:
        messages: 消息列表，每条消息包含：
            - role: "user" | "assistant" | "system" | "tool"
            - content: 消息内容
            - timestamp: 时间戳（可选）
            - tool_calls: 工具调用（可选）
        session_key: 会话标识
        summary: 对话摘要（可选，如果 auto_generate_summary=True 则自动生成）
        auto_generate_summary: 是否自动生成详细摘要
    
    返回:
        保存结果
    """
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record_dir = get_chat_record_dir()
        
        # 自动生成详细摘要
        if auto_generate_summary or not summary or len(summary) < 10:
            summary = generate_detailed_summary(messages)
        
        # ========== 保存 JSON 格式（完整记录） ==========
        json_file = record_dir / f"{today}.json"
        
        # 加载现有记录
        records = []
        if json_file.exists():
            try:
                records = json.loads(json_file.read_text(encoding="utf-8"))
            except:
                records = []
        
        # 添加新记录
        chat_record = {
            "session_key": session_key,
            "timestamp": timestamp,
            "message_count": len(messages),
            "messages": messages,
            "summary": summary,
        }
        records.append(chat_record)
        
        # 保存 JSON
        json_file.write_text(
            json.dumps(records, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        
        # ========== 保存 Markdown 格式（摘要） ==========
        md_file = record_dir / f"{today}.md"
        
        # 确保文件存在
        if not md_file.exists():
            md_file.write_text(
                f"# {today} - 每日记忆\n\n_每日发生的原始日志。_\n\n---\n\n",
                encoding="utf-8"
            )
        
        # 生成摘要
        if not summary:
            # 自动提取摘要
            user_messages = [m for m in messages if m.get("role") == "user"]
            if user_messages:
                summary = f"对话包含 {len(user_messages)} 条用户消息"
            else:
                summary = "系统对话记录"
        
        # 添加到 Markdown 文件
        md_entry = f"""
### {timestamp} - 对话记录

**会话：** {session_key}

**消息数：** {len(messages)} 条

**摘要：** {summary}

**详情：** 查看 `{today}.json`

---

"""
        
        # 追加到文件
        with open(md_file, "a", encoding="utf-8") as f:
            f.write(md_entry)
        
        logger.info(f"✓ 保存聊天记录：{len(messages)} 条消息 → {today}.json")
        
        return {
            "success": True,
            "message": f"✓ 已保存 {len(messages)} 条消息",
            "json_file": str(json_file),
            "md_file": str(md_file),
            "date": today,
        }
    
    except Exception as e:
        logger.error(f"保存聊天记录失败：{e}")
        return {
            "success": False,
            "error": f"保存失败：{e}",
        }


def append_chat_summary(
    summary: str,
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """
    添加对话摘要到今日记忆
    
    参数:
        summary: 摘要内容
        title: 可选标题
    
    返回:
        保存结果
    """
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        timestamp = datetime.now().strftime("%H:%M")
        record_dir = get_chat_record_dir()
        md_file = record_dir / f"{today}.md"
        
        # 确保文件存在
        if not md_file.exists():
            md_file.write_text(
                f"# {today} - 每日记忆\n\n_每日发生的原始日志。_\n\n---\n\n",
                encoding="utf-8"
            )
        
        # 添加摘要
        if title:
            entry = f"### {timestamp} - {title}\n\n{summary}\n\n---\n\n"
        else:
            entry = f"### {timestamp} - 对话摘要\n\n{summary}\n\n---\n\n"
        
        # 追加到文件
        with open(md_file, "a", encoding="utf-8") as f:
            f.write(entry)
        
        logger.info(f"✓ 添加对话摘要：{summary[:50]}...")
        
        return {
            "success": True,
            "message": f"✓ 已添加摘要到 {today}.md",
            "file": str(md_file),
        }
    
    except Exception as e:
        logger.error(f"添加摘要失败：{e}")
        return {
            "success": False,
            "error": f"添加失败：{e}",
        }


def get_today_records(limit: int = 10) -> Dict[str, Any]:
    """
    获取今日聊天记录
    
    参数:
        limit: 最大返回记录数
    
    返回:
        记录列表
    """
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        record_dir = get_chat_record_dir()
        json_file = record_dir / f"{today}.json"
        
        if not json_file.exists():
            return {
                "success": True,
                "message": "今日暂无聊天记录",
                "records": [],
            }
        
        records = json.loads(json_file.read_text(encoding="utf-8"))
        
        # 返回最近的记录
        recent_records = records[-limit:] if len(records) > limit else records
        
        return {
            "success": True,
            "message": f"找到 {len(recent_records)} 条记录",
            "records": recent_records,
            "total": len(records),
        }
    
    except Exception as e:
        logger.error(f"获取记录失败：{e}")
        return {
            "success": False,
            "error": f"获取失败：{e}",
        }
