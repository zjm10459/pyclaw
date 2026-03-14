#!/usr/bin/env python3
"""
记忆工具
========

让 AI 可以主动保存重要信息到长期记忆。

功能：
- remember: 保存重要信息到长期记忆
- update_memory: 更新现有记忆
- search_memory: 搜索记忆

使用场景：
- 用户说"记住这个"
- AI 学到重要教训
- 记录关键决策
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger("pyclaw.memory_tools")


def get_memory_file() -> Path:
    """获取长期记忆文件路径"""
    # 优先使用 PyClaw 项目工作区
    pyclaw_workspace = Path.home() / ".openclaw" / "workspace" / "pyclaw"
    memory_file = pyclaw_workspace / "长期记忆.md"
    
    # 如果不存在，尝试 ~/.pyclaw/workspace
    if not memory_file.exists():
        workspace = Path.home() / ".pyclaw" / "workspace"
        memory_file = workspace / "长期记忆.md"
    
    # 最后尝试 OpenClaw 工作区
    if not memory_file.exists():
        memory_file = Path.home() / ".openclaw" / "workspace" / "长期记忆.md"
    
    return memory_file


def get_daily_memory_file() -> Path:
    """获取今日记忆文件路径"""
    # PyClaw 项目根目录的 memory_chat 目录
    memory_dir = Path.home() / ".openclaw" / "workspace" / "pyclaw" / "memory_chat"
    
    # 如果不存在，尝试旧路径
    if not memory_dir.exists():
        memory_dir = Path.home() / ".pyclaw" / "workspace" / "pyclaw" / "memory_chat"
    
    # 最后回退到 ~/.pyclaw/memory_chat
    if not memory_dir.exists():
        memory_dir = Path.home() / ".pyclaw" / "memory_chat"
    
    memory_dir.mkdir(parents=True, exist_ok=True)
    
    today = datetime.now().strftime("%Y-%m-%d")
    return memory_dir / f"{today}.md"


def remember(
    content: str,
    category: str = "general",
    tags: Optional[list] = None,
) -> dict:
    """
    保存重要信息到长期记忆
    
    参数:
        content: 要记住的内容
        category: 分类（general, decision, lesson, preference, context 等）
        tags: 标签列表
    
    返回:
        保存结果
    """
    try:
        memory_file = get_memory_file()
        
        # 确保文件存在
        if not memory_file.exists():
            memory_file.parent.mkdir(parents=True, exist_ok=True)
            memory_file.write_text(
                "# 长期记忆.md\n\n_这是精选的记忆，记录重要的决策、上下文和偏好。_\n\n---\n\n",
                encoding="utf-8"
            )
        
        # 读取现有内容
        content_existing = memory_file.read_text(encoding="utf-8")
        
        # 添加新记忆
        today = datetime.now().strftime("%Y-%m-%d")
        tags_str = ", ".join(tags) if tags else ""
        
        new_memory = f"""
## 📅 {today}

### {category}

{content}

"""
        if tags_str:
            new_memory += f"**标签：** {tags_str}\n\n"
        
        new_memory += "---\n\n"
        
        # 追加到文件
        with open(memory_file, "a", encoding="utf-8") as f:
            f.write(new_memory)
        
        logger.info(f"✓ 保存记忆到长期记忆：{content[:50]}...")
        
        return {
            "success": True,
            "message": f"✓ 已保存到长期记忆",
            "category": category,
            "content": content[:100] + "..." if len(content) > 100 else content,
        }
    
    except Exception as e:
        logger.error(f"保存记忆失败：{e}")
        return {
            "success": False,
            "error": f"保存记忆失败：{e}",
        }


def append_to_daily_memory(
    content: str,
    title: Optional[str] = None,
) -> dict:
    """
    添加到今日记忆（每日笔记）
    
    参数:
        content: 内容
        title: 可选标题
    
    返回:
        保存结果
    """
    try:
        memory_file = get_daily_memory_file()
        
        # 确保文件存在
        if not memory_file.exists():
            today = datetime.now().strftime("%Y-%m-%d")
            memory_file.write_text(
                f"# {today} - 每日记忆\n\n_每日发生的原始日志。_\n\n---\n\n",
                encoding="utf-8"
            )
        
        # 添加内容
        timestamp = datetime.now().strftime("%H:%M")
        
        if title:
            new_entry = f"### {timestamp} - {title}\n\n{content}\n\n---\n\n"
        else:
            new_entry = f"### {timestamp}\n\n{content}\n\n---\n\n"
        
        # 追加到文件
        with open(memory_file, "a", encoding="utf-8") as f:
            f.write(new_entry)
        
        logger.info(f"✓ 添加到今日记忆：{content[:50]}...")
        
        return {
            "success": True,
            "message": f"✓ 已添加到今日记忆 ({memory_file.name})",
            "content": content[:100] + "..." if len(content) > 100 else content,
        }
    
    except Exception as e:
        logger.error(f"添加到今日记忆失败：{e}")
        return {
            "success": False,
            "error": f"添加失败：{e}",
        }


def search_memory(query: str, limit: int = 5) -> dict:
    """
    搜索长期记忆
    
    参数:
        query: 搜索关键词
        limit: 最大结果数
    
    返回:
        搜索结果
    """
    try:
        memory_file = get_memory_file()
        
        if not memory_file.exists():
            return {
                "success": True,
                "message": "长期记忆为空",
                "results": [],
            }
        
        content = memory_file.read_text(encoding="utf-8")
        
        # 简单关键词搜索
        results = []
        lines = content.split("\n")
        
        for i, line in enumerate(lines):
            if query.lower() in line.lower():
                # 获取上下文（前后各 3 行）
                start = max(0, i - 3)
                end = min(len(lines), i + 4)
                context = "\n".join(lines[start:end])
                results.append({
                    "line": i + 1,
                    "match": line.strip(),
                    "context": context,
                })
                
                if len(results) >= limit:
                    break
        
        return {
            "success": True,
            "message": f"找到 {len(results)} 条相关记忆",
            "results": results,
        }
    
    except Exception as e:
        logger.error(f"搜索记忆失败：{e}")
        return {
            "success": False,
            "error": f"搜索失败：{e}",
        }


def register_all(tool_registry: Any) -> int:
    """
    注册所有记忆工具
    
    参数:
        tool_registry: ToolRegistry 实例
    
    返回:
        注册的工具数量
    """
    count = 0
    
    from tools.registry import tool
    
    # ========== 注册 remember 工具 ==========
    @tool(
        name="remember",
        description="保存重要信息到长期记忆。当用户说'记住这个'、'不要忘记'或 AI 学到重要教训时使用。参数：content=要记住的内容，category=分类（general/decision/lesson/preference/context），tags=标签列表。",
        parameters={
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "要记住的内容",
                },
                "category": {
                    "type": "string",
                    "description": "分类（general, decision, lesson, preference, context 等）",
                    "default": "general",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "标签列表",
                },
            },
            "required": ["content"],
        },
    )
    def remember_tool(
        content: str,
        category: str = "general",
        tags: Optional[list] = None,
        **kwargs
    ) -> dict:
        """保存重要信息到长期记忆"""
        return remember(content, category, tags)
    
    tool_registry.register_tool(remember_tool)
    count += 1
    logger.info(f"✓ 注册记忆工具：remember")
    
    # ========== 注册 append_to_daily_memory 工具 ==========
    @tool(
        name="append_to_daily_memory",
        description="添加到今日记忆（每日笔记）。记录当天发生的事件、对话摘要等。参数：content=内容，title=可选标题。",
        parameters={
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "要记录的内容",
                },
                "title": {
                    "type": "string",
                    "description": "可选标题",
                },
            },
            "required": ["content"],
        },
    )
    def daily_memory_tool(
        content: str,
        title: Optional[str] = None,
        **kwargs
    ) -> dict:
        """添加到今日记忆"""
        return append_to_daily_memory(content, title)
    
    tool_registry.register_tool(daily_memory_tool)
    count += 1
    logger.info(f"✓ 注册记忆工具：append_to_daily_memory")
    
    # ========== 注册 search_memory 工具 ==========
    @tool(
        name="search_memory",
        description="搜索长期记忆。当需要查找之前记录的信息时使用。参数：query=搜索关键词，limit=最大结果数（默认 5）。",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词",
                },
                "limit": {
                    "type": "integer",
                    "description": "最大结果数",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    )
    def search_memory_tool(
        query: str,
        limit: int = 5,
        **kwargs
    ) -> dict:
        """搜索长期记忆"""
        return search_memory(query, limit)
    
    tool_registry.register_tool(search_memory_tool)
    count += 1
    logger.info(f"✓ 注册记忆工具：search_memory")
    
    return count
