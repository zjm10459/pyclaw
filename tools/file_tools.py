"""
文件系统工具
============

提供文件操作相关的工具。

功能：
- 读取文件内容
- 写入文件
- 编辑文件（精确替换）
- 列出目录
- 删除文件
- 搜索文件

安全说明：
- 默认限制在工作区目录内
- 支持配置允许的路径
- 敏感操作需要确认
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from tools.registry import tool, ToolContext

logger = logging.getLogger("pyclaw.tools.files")


# ==================== 配置 ====================

# 默认工作区目录
DEFAULT_WORKSPACE = Path.home() / ".pyclaw" / "workspace"

# 允许访问的根目录（可配置）
ALLOWED_ROOTS = [
    DEFAULT_WORKSPACE,
    Path("/tmp"),
]


def _is_safe_path(path: Path, context: Optional[ToolContext] = None) -> bool:
    """
    检查路径是否安全（在允许的目录内）
    
    参数:
        path: 要检查的路径
        context: 工具上下文
    
    返回:
        True（安全）或 False（不安全）
    """
    # 解析绝对路径
    abs_path = path.resolve()
    
    # 检查工作区
    if context and context.workspace:
        workspace = Path(context.workspace).resolve()
        if str(abs_path).startswith(str(workspace)):
            return True
    
    # 检查其他允许的根目录
    for root in ALLOWED_ROOTS:
        if str(abs_path).startswith(str(root.resolve())):
            return True
    
    return False


def _read_file_safe(path: Path, encoding: str = "utf-8") -> str:
    """
    安全读取文件
    
    参数:
        path: 文件路径
        encoding: 编码格式
    
    返回:
        文件内容
    """
    # 检查文件大小（限制 10MB）
    max_size = 10 * 1024 * 1024
    if path.stat().st_size > max_size:
        raise ValueError(f"文件过大（{path.stat().st_size} 字节），最大支持 10MB")
    
    # 读取内容
    with open(path, 'r', encoding=encoding, errors='replace') as f:
        return f.read()


@tool(
    name="read_file",
    description="读取文件内容，支持大文件分块读取",
)
def read_file(
    path: str,
    offset: int = 0,
    limit: int = 2000,
    encoding: str = "utf-8",
    context: Optional[ToolContext] = None,
) -> str:
    """
    读取文件内容
    
    参数:
        path: 文件路径
        offset: 起始行号（从 0 开始）
        limit: 最大读取行数
        encoding: 编码格式
        context: 工具上下文
    
    返回:
        文件内容
    
    示例:
        read_file("/path/to/file.txt")
        read_file("/path/to/file.txt", offset=100, limit=500)
    """
    file_path = Path(path)
    
    # 安全检查
    if not _is_safe_path(file_path, context):
        return f"❌ 错误：路径不在允许范围内\n允许的路径：{[str(r) for r in ALLOWED_ROOTS]}"
    
    if not file_path.exists():
        return f"❌ 错误：文件不存在：{path}"
    
    if not file_path.is_file():
        return f"❌ 错误：不是文件：{path}"
    
    try:
        # 读取文件
        content = _read_file_safe(file_path, encoding)
        
        # 按行分割
        lines = content.splitlines()
        
        # 应用偏移和限制
        if offset > 0 or limit < len(lines):
            selected_lines = lines[offset:offset + limit]
            result = "\n".join(selected_lines)
            
            # 添加信息
            total = len(lines)
            result = f"[第 {offset + 1}-{offset + len(selected_lines)} 行，共 {total} 行]\n\n{result}"
            
            if offset + limit < total:
                result += f"\n\n[还有 {total - offset - limit} 行未显示，使用 offset={offset + limit} 继续]"
        else:
            result = content
        
        return result
    
    except Exception as e:
        logger.exception(f"读取文件失败：{e}")
        return f"❌ 错误：{e}"


@tool(
    name="write_file",
    description="写入文件内容，如果文件存在则覆盖",
)
def write_file(
    path: str,
    content: str,
    encoding: str = "utf-8",
    context: Optional[ToolContext] = None,
) -> str:
    """
    写入文件内容
    
    参数:
        path: 文件路径
        content: 文件内容
        encoding: 编码格式
        context: 工具上下文
    
    返回:
        操作结果
    
    示例:
        write_file("/path/to/file.txt", "Hello World")
    """
    file_path = Path(path)
    
    # 安全检查
    if not _is_safe_path(file_path, context):
        return f"❌ 错误：路径不在允许范围内"
    
    try:
        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        
        return f"✅ 文件已写入：{path}\n大小：{len(content)} 字节"
    
    except Exception as e:
        logger.exception(f"写入文件失败：{e}")
        return f"❌ 错误：{e}"


@tool(
    name="edit_file",
    description="编辑文件，精确替换指定文本",
)
def edit_file(
    path: str,
    old_text: str,
    new_text: str,
    encoding: str = "utf-8",
    context: Optional[ToolContext] = None,
) -> str:
    """
    编辑文件（精确替换）
    
    参数:
        path: 文件路径
        old_text: 要替换的原文本（必须完全匹配）
        new_text: 新文本
        encoding: 编码格式
        context: 工具上下文
    
    返回:
        操作结果
    
    示例:
        edit_file("/path/to/file.txt", "old text", "new text")
    """
    file_path = Path(path)
    
    # 安全检查
    if not _is_safe_path(file_path, context):
        return f"❌ 错误：路径不在允许范围内"
    
    if not file_path.exists():
        return f"❌ 错误：文件不存在：{path}"
    
    try:
        # 读取文件
        content = _read_file_safe(file_path, encoding)
        
        # 检查原文本是否存在
        if old_text not in content:
            return f"❌ 错误：未找到要替换的文本\n请检查文本是否完全匹配（包括空格和换行）"
        
        # 替换文本
        new_content = content.replace(old_text, new_text, 1)
        
        # 写回文件
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(new_content)
        
        return f"✅ 文件已编辑：{path}\n替换了 {len(old_text)} 字符"
    
    except Exception as e:
        logger.exception(f"编辑文件失败：{e}")
        return f"❌ 错误：{e}"


@tool(
    name="list_directory",
    description="列出目录内容",
)
def list_directory(
    path: str = ".",
    recursive: bool = False,
    max_depth: int = 3,
    context: Optional[ToolContext] = None,
) -> str:
    """
    列出目录内容
    
    参数:
        path: 目录路径
        recursive: 是否递归列出
        max_depth: 最大递归深度
        context: 工具上下文
    
    返回:
        目录内容列表
    
    示例:
        list_directory("/path/to/dir")
        list_directory("/path/to/dir", recursive=True, max_depth=2)
    """
    dir_path = Path(path)
    
    # 安全检查
    if not _is_safe_path(dir_path, context):
        return f"❌ 错误：路径不在允许范围内"
    
    if not dir_path.exists():
        return f"❌ 错误：目录不存在：{path}"
    
    if not dir_path.is_dir():
        return f"❌ 错误：不是目录：{path}"
    
    try:
        result = []
        
        if recursive:
            # 递归列出
            def walk_dir(path: Path, depth: int, prefix: str = ""):
                if depth > max_depth:
                    return
                
                try:
                    items = sorted(path.iterdir())
                    for i, item in enumerate(items):
                        is_last = (i == len(items) - 1)
                        connector = "└── " if is_last else "├── "
                        
                        # 跳过隐藏文件和目录
                        if item.name.startswith('.') and item.name != '.':
                            continue
                        
                        result.append(f"{prefix}{connector}{item.name}")
                        
                        if item.is_dir():
                            next_prefix = prefix + ("    " if is_last else "│   ")
                            walk_dir(item, depth + 1, next_prefix)
                except PermissionError:
                    pass
            
            walk_dir(dir_path, 0)
        else:
            # 只列出当前目录
            items = sorted(dir_path.iterdir())
            for item in items:
                # 跳过隐藏文件
                if item.name.startswith('.') and item.name != '.':
                    continue
                
                suffix = "/" if item.is_dir() else ""
                result.append(f"{item.name}{suffix}")
        
        return f"📁 {dir_path}\n\n" + "\n".join(result)
    
    except Exception as e:
        logger.exception(f"列出目录失败：{e}")
        return f"❌ 错误：{e}"


@tool(
    name="delete_file",
    description="删除文件或目录（谨慎使用）",
)
def delete_file(
    path: str,
    recursive: bool = False,
    context: Optional[ToolContext] = None,
) -> str:
    """
    删除文件或目录
    
    参数:
        path: 文件/目录路径
        recursive: 是否递归删除（目录需要）
        context: 工具上下文
    
    返回:
        操作结果
    
    示例:
        delete_file("/path/to/file.txt")
        delete_file("/path/to/dir", recursive=True)
    """
    file_path = Path(path)
    
    # 安全检查
    if not _is_safe_path(file_path, context):
        return f"❌ 错误：路径不在允许范围内"
    
    if not file_path.exists():
        return f"❌ 错误：文件/目录不存在：{path}"
    
    try:
        if file_path.is_file():
            # 删除文件
            file_path.unlink()
            return f"✅ 文件已删除：{path}"
        
        elif file_path.is_dir():
            if not recursive:
                return f"❌ 错误：删除目录需要 recursive=True"
            
            # 删除目录
            shutil.rmtree(file_path)
            return f"✅ 目录已删除：{path}"
        
        else:
            return f"❌ 错误：未知的文件类型：{path}"
    
    except Exception as e:
        logger.exception(f"删除失败：{e}")
        return f"❌ 错误：{e}"


@tool(
    name="search_files",
    description="搜索文件（按名称或扩展名）",
)
def search_files(
    pattern: str,
    path: str = ".",
    file_type: Optional[str] = None,
    max_results: int = 50,
    context: Optional[ToolContext] = None,
) -> str:
    """
    搜索文件
    
    参数:
        pattern: 搜索模式（支持通配符 *）
        path: 搜索根目录
        file_type: 文件类型过滤（如 "py", "md"）
        max_results: 最大结果数
        context: 工具上下文
    
    返回:
        匹配的文件列表
    
    示例:
        search_files("*.py", "/path/to/project")
        search_files("README", file_type="md")
    """
    search_path = Path(path)
    
    # 安全检查
    if not _is_safe_path(search_path, context):
        return f"❌ 错误：路径不在允许范围内"
    
    try:
        results = []
        
        # 递归搜索
        for file in search_path.rglob(pattern):
            if not file.is_file():
                continue
            
            # 过滤文件类型
            if file_type and file.suffix != f".{file_type}":
                continue
            
            # 跳过隐藏文件
            if file.name.startswith('.'):
                continue
            
            results.append(str(file))
            
            if len(results) >= max_results:
                break
        
        if not results:
            return f"📭 未找到匹配的文件"
        
        # 格式化输出
        output = f"🔍 找到 {len(results)} 个文件:\n\n"
        for file in results:
            # 显示相对路径
            try:
                rel_path = file.relative_to(search_path)
            except ValueError:
                rel_path = file
            
            # 显示文件大小
            size = file.stat().st_size
            size_str = f"{size / 1024:.1f}KB" if size < 1024 * 1024 else f"{size / 1024 / 1024:.1f}MB"
            
            output += f"📄 {rel_path} ({size_str})\n"
        
        return output
    
    except Exception as e:
        logger.exception(f"搜索失败：{e}")
        return f"❌ 错误：{e}"


@tool(
    name="file_info",
    description="获取文件信息（大小、修改时间等）",
)
def file_info(path: str, context: Optional[ToolContext] = None) -> str:
    """
    获取文件信息
    
    参数:
        path: 文件路径
        context: 工具上下文
    
    返回:
        文件信息
    
    示例:
        file_info("/path/to/file.txt")
    """
    file_path = Path(path)
    
    # 安全检查
    if not _is_safe_path(file_path, context):
        return f"❌ 错误：路径不在允许范围内"
    
    if not file_path.exists():
        return f"❌ 错误：文件不存在：{path}"
    
    try:
        stat = file_path.stat()
        
        # 格式化大小
        size = stat.st_size
        if size < 1024:
            size_str = f"{size} B"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size / 1024 / 1024:.1f} MB"
        
        # 格式化时间
        from datetime import datetime
        mtime = datetime.fromtimestamp(stat.st_mtime)
        mtime_str = mtime.strftime("%Y-%m-%d %H:%M:%S")
        
        # 构建信息
        info = {
            "路径": str(file_path.absolute()),
            "类型": "目录" if file_path.is_dir() else "文件",
            "大小": size_str,
            "修改时间": mtime_str,
            "权限": oct(stat.st_mode)[-3:],
        }
        
        output = "📊 文件信息:\n\n"
        for key, value in info.items():
            output += f"  {key}: {value}\n"
        
        return output
    
    except Exception as e:
        logger.exception(f"获取信息失败：{e}")
        return f"❌ 错误：{e}"


# 导出所有工具
__all__ = [
    "read_file",
    "write_file",
    "edit_file",
    "list_directory",
    "delete_file",
    "search_files",
    "file_info",
    "register_all",
]


def register_all(registry):
    """
    注册所有文件工具到注册表
    
    参数:
        registry: ToolRegistry 实例
    """
    from tools.registry import ToolDefinition
    
    tools = [
        read_file,
        write_file,
        edit_file,
        list_directory,
        delete_file,
        search_files,
        file_info,
    ]
    
    for tool_func in tools:
        if hasattr(tool_func, '_tool_definition'):
            registry.register(tool_func)
        else:
            logger.warning(f"工具 {tool_func.__name__} 没有工具定义，跳过注册")
