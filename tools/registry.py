"""
工具注册表
==========

管理所有可用工具的注册、发现和调用。
"""

import inspect
import json
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from functools import wraps
import logging

logger = logging.getLogger("pyclaw.tools")


@dataclass
class ToolDefinition:
    """
    工具定义
    
    描述一个工具的元数据和调用方式。
    
    属性:
        name: 工具名称
        description: 工具描述
        function: 实际执行的函数
        parameters: JSON Schema 格式的参数定义
        requires_context: 是否需要上下文
    """
    name: str
    description: str
    function: Callable
    parameters: Dict[str, Any]
    requires_context: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典（用于发送给 LLM）
        
        返回:
            工具定义字典
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass
class ToolContext:
    """
    工具执行上下文
    
    提供给工具函数的运行时信息。
    
    属性:
        session_key: 当前会话键
        agent_id: 当前代理 ID
        workspace: 工作区路径
        config: 配置对象
        variables: 自定义变量
    """
    session_key: str
    agent_id: str
    workspace: str
    config: Optional[Dict[str, Any]] = None
    variables: Dict[str, Any] = field(default_factory=dict)


def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
):
    """
    工具装饰器
    
    将普通函数注册为工具。
    
    参数:
        name: 工具名称（默认函数名）
        description: 工具描述（默认 docstring）
        parameters: JSON Schema 参数（默认从函数签名推断）
    
    使用示例:
        @tool(name="read_file", description="读取文件内容")
        def read_file(path: str) -> str:
            with open(path, 'r') as f:
                return f.read()
    """
    def decorator(func: Callable) -> Callable:
        tool_name = name or func.__name__
        tool_desc = description or (func.__doc__ or "").strip()
        
        # 如果没有提供参数，从函数签名推断
        tool_params = parameters or infer_parameters(func)
        
        # 创建工具定义
        tool_def = ToolDefinition(
            name=tool_name,
            description=tool_desc,
            function=func,
            parameters=tool_params,
        )
        
        # 附加到函数上（便于后续访问）
        func._tool_definition = tool_def
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def infer_parameters(func: Callable) -> Dict[str, Any]:
    """
    从函数签名推断 JSON Schema 参数
    
    参数:
        func: 函数对象
    
    返回:
        JSON Schema 对象
    """
    sig = inspect.signature(func)
    
    properties = {}
    required = []
    
    for param_name, param in sig.parameters.items():
        # 跳过 self 和 context 参数
        if param_name in ("self", "context"):
            continue
        
        # 推断类型
        param_type = "string"  # 默认
        
        if param.annotation != inspect.Parameter.empty:
            if param.annotation == int:
                param_type = "integer"
            elif param.annotation == float:
                param_type = "number"
            elif param.annotation == bool:
                param_type = "boolean"
            elif param.annotation == list:
                param_type = "array"
            elif param.annotation == dict:
                param_type = "object"
        
        # 添加属性
        properties[param_name] = {
            "type": param_type,
            "description": f"参数：{param_name}",
        }
        
        # 检查是否必需
        if param.default == inspect.Parameter.empty:
            required.append(param_name)
    
    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


class ToolRegistry:
    """
    工具注册表
    
    管理所有可用工具的注册、查询和调用。
    
    属性:
        tools: 工具字典 {name: ToolDefinition}
    """
    
    def __init__(self):
        """初始化工具注册表"""
        self.tools: Dict[str, ToolDefinition] = {}
        
        # 注册内置工具
        self._register_builtin_tools()
    
    def _register_builtin_tools(self):
        """注册内置工具"""
        
        @self.register
        @tool(
            name="echo",
            description="回显消息（测试工具）",
            parameters={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "要回显的消息",
                    },
                },
                "required": ["message"],
            },
        )
        def echo(message: str, context: Optional[ToolContext] = None) -> str:
            """回显消息"""
            logger.info(f"Echo: {message}")
            return f"Echo: {message}"
        
        @self.register
        @tool(
            name="get_time",
            description="获取当前时间",
        )
        def get_time(context: Optional[ToolContext] = None) -> str:
            """获取当前时间"""
            from datetime import datetime
            now = datetime.now()
            return now.strftime("%Y-%m-%d %H:%M:%S")
        
        @self.register
        @tool(
            name="list_tools",
            description="列出所有可用工具",
        )
        def list_tools(context: Optional[ToolContext] = None) -> str:
            """列出工具"""
            tools_info = []
            for name, tool_def in self.tools.items():
                tools_info.append(f"- {name}: {tool_def.description}")
            return "\n".join(tools_info)
    
    def register(
        self,
        func_or_def: Optional[Callable | ToolDefinition] = None,
        name: Optional[str] = None,
    ) -> Callable:
        """
        注册工具
        
        可以作为装饰器使用，也可以直接传入 ToolDefinition。
        
        参数:
            func_or_def: 函数或工具定义
            name: 工具名称（覆盖）
        
        返回:
            装饰器函数
        
        使用示例:
            # 方式 1：装饰器
            @registry.register
            def my_tool():
                pass
            
            # 方式 2：直接注册
            registry.register(tool_def)
        """
        if isinstance(func_or_def, ToolDefinition):
            # 直接注册 ToolDefinition
            tool_def = func_or_def
            if name:
                tool_def.name = name
            self.tools[tool_def.name] = tool_def
            logger.info(f"注册工具：{tool_def.name}")
            return lambda f: f
        
        elif callable(func_or_def):
            # 作为装饰器
            func = func_or_def
            
            # 获取工具定义
            if hasattr(func, '_tool_definition'):
                tool_def = func._tool_definition
            else:
                # 自动创建
                tool_def = ToolDefinition(
                    name=name or func.__name__,
                    description=(func.__doc__ or "").strip(),
                    function=func,
                    parameters=infer_parameters(func),
                )
            
            if name:
                tool_def.name = name
            
            self.tools[tool_def.name] = tool_def
            logger.info(f"注册工具：{tool_def.name}")
            
            return func
        
        else:
            # 返回装饰器
            def decorator(func: Callable) -> Callable:
                return self.register(func, name=name)
            
            return decorator
    
    def get(self, name: str) -> Optional[ToolDefinition]:
        """
        获取工具定义
        
        参数:
            name: 工具名称
        
        返回:
            工具定义或 None
        """
        return self.tools.get(name)
    
    def list_tools(self) -> List[ToolDefinition]:
        """
        列出所有工具（返回 ToolDefinition 对象）
        
        返回:
            工具定义列表
        """
        return list(self.tools.values())
    
    def get_schema(self) -> List[Dict[str, Any]]:
        """
        获取工具 Schema（用于 LLM 调用）
        
        返回:
            JSON Schema 列表（OpenAI 格式）
        """
        return [tool_def.to_dict() for tool_def in self.tools.values()]
    
    async def call(
        self,
        name: str,
        arguments: Dict[str, Any],
        context: Optional[ToolContext] = None,
    ) -> Any:
        """
        调用工具
        
        参数:
            name: 工具名称
            arguments: 参数字典
            context: 工具上下文
        
        返回:
            工具执行结果
        
        异常:
            ValueError: 工具不存在
            Exception: 工具执行错误
        """
        tool_def = self.get(name)
        
        if not tool_def:
            raise ValueError(f"工具不存在：{name}")
        
        logger.info(f"调用工具：{name}({arguments})")
        
        try:
            # 检查是否需要上下文
            sig = inspect.signature(tool_def.function)
            if 'context' in sig.parameters:
                result = tool_def.function(**arguments, context=context)
            else:
                result = tool_def.function(**arguments)
            
            # 如果是协程，等待结果
            if inspect.iscoroutine(result):
                result = await result
            
            logger.info(f"工具完成：{name}")
            return result
        
        except Exception as e:
            logger.exception(f"工具执行失败：{name}: {e}")
            raise
    
    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """
        获取工具 Schema（用于 LLM）
        
        返回:
            工具 Schema 列表
        """
        return [tool_def.to_dict() for tool_def in self.tools.values()]


# 全局默认注册表
_default_registry: Optional[ToolRegistry] = None

def get_default_registry() -> ToolRegistry:
    """获取默认工具注册表"""
    global _default_registry
    if _default_registry is None:
        _default_registry = ToolRegistry()
    return _default_registry
