#!/usr/bin/env python3
"""
PyClaw 异常定义
===============

统一的异常处理体系
"""


class PyClawError(Exception):
    """PyClaw 基础异常"""
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code or "PYCLAW_ERROR"
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "error": self.code,
            "message": self.message,
        }


class ConfigError(PyClawError):
    """配置错误"""
    def __init__(self, message: str):
        super().__init__(message, code="CONFIG_ERROR")


class ToolError(PyClawError):
    """工具错误"""
    def __init__(self, message: str, tool_name: str = None):
        self.tool_name = tool_name
        message = f"工具 {tool_name}: {message}" if tool_name else message
        super().__init__(message, code="TOOL_ERROR")


class MemoryError(PyClawError):
    """记忆系统错误"""
    def __init__(self, message: str):
        super().__init__(message, code="MEMORY_ERROR")


class AgentError(PyClawError):
    """Agent 错误"""
    def __init__(self, message: str, agent_name: str = None):
        self.agent_name = agent_name
        message = f"Agent {agent_name}: {message}" if agent_name else message
        super().__init__(message, code="AGENT_ERROR")


class ChannelError(PyClawError):
    """渠道错误"""
    def __init__(self, message: str, channel: str = None):
        self.channel = channel
        message = f"渠道 {channel}: {message}" if channel else message
        super().__init__(message, code="CHANNEL_ERROR")


class GatewayError(PyClawError):
    """Gateway 错误"""
    def __init__(self, message: str):
        super().__init__(message, code="GATEWAY_ERROR")


class AuthenticationError(PyClawError):
    """认证错误"""
    def __init__(self, message: str):
        super().__init__(message, code="AUTH_ERROR")


class ValidationError(PyClawError):
    """验证错误"""
    def __init__(self, message: str, field: str = None):
        self.field = field
        message = f"{field}: {message}" if field else message
        super().__init__(message, code="VALIDATION_ERROR")


class ResourceNotFoundError(PyClawError):
    """资源未找到错误"""
    def __init__(self, resource_type: str, resource_id: str = None):
        message = f"{resource_type} 未找到"
        if resource_id:
            message += f": {resource_id}"
        super().__init__(message, code="RESOURCE_NOT_FOUND")


class PermissionError(PyClawError):
    """权限错误"""
    def __init__(self, message: str, action: str = None):
        self.action = action
        message = f"{action}: {message}" if action else message
        super().__init__(message, code="PERMISSION_ERROR")


class ExternalServiceError(PyClawError):
    """外部服务错误"""
    def __init__(self, message: str, service: str = None):
        self.service = service
        message = f"外部服务 {service}: {message}" if service else message
        super().__init__(message, code="EXTERNAL_SERVICE_ERROR")


class RateLimitError(PyClawError):
    """频率限制错误"""
    def __init__(self, message: str = "请求频率超限"):
        super().__init__(message, code="RATE_LIMIT_ERROR")


class TimeoutError(PyClawError):
    """超时错误"""
    def __init__(self, message: str = "操作超时", operation: str = None):
        self.operation = operation
        message = f"{operation} 超时" if operation else message
        super().__init__(message, code="TIMEOUT_ERROR")


# ============================================================================
# 异常处理装饰器
# ============================================================================

import functools
import logging

logger = logging.getLogger("pyclaw.exceptions")


def handle_exceptions(default_return=None, reraise: bool = False):
    """
    异常处理装饰器
    
    参数:
        default_return: 异常时的默认返回值
        reraise: 是否重新抛出异常
    
    使用示例:
        @handle_exceptions(default_return=[])
        def risky_function():
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except PyClawError as e:
                logger.error(f"{func.__name__}: {e.message}")
                if reraise:
                    raise
                return default_return
            except Exception as e:
                logger.exception(f"{func.__name__}: 未预期的错误 - {e}")
                if reraise:
                    raise
                return default_return
        return wrapper
    return decorator


def validate_params(**validators):
    """
    参数验证装饰器
    
    参数:
        validators: 验证函数字典
    
    使用示例:
        @validate_params(name=lambda x: len(x) > 0, age=lambda x: x > 0)
        def create_user(name, age):
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import inspect
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            
            for param_name, validator in validators.items():
                if param_name in bound.arguments:
                    value = bound.arguments[param_name]
                    if not validator(value):
                        raise ValidationError(
                            f"参数验证失败",
                            field=param_name
                        )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
