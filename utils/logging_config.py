#!/usr/bin/env python3
"""
PyClaw 日志配置
===============

统一的日志系统，支持：
- 控制台输出
- 文件轮转
- 结构化日志
- 多级别日志
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """
    彩色日志格式化器
    
    不同级别使用不同颜色
    """
    
    # ANSI 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[32m',      # 绿色
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 红色
        'CRITICAL': '\033[35m',  # 紫色
        'RESET': '\033[0m',      # 重置
    }
    
    def format(self, record):
        """格式化日志记录"""
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


class StructuredFormatter(logging.Formatter):
    """
    结构化日志格式化器（JSON 格式）
    
    适合机器解析和日志分析系统
    """
    
    def format(self, record):
        """格式化日志记录为 JSON"""
        import json
        
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # 添加额外字段
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    use_color: bool = True,
    use_structured: bool = False,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> logging.Logger:
    """
    配置日志系统
    
    参数:
        level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        log_file: 日志文件路径（None 表示只输出到控制台）
        use_color: 是否使用彩色输出
        use_structured: 是否使用结构化日志（JSON 格式）
        max_bytes: 单个日志文件最大大小
        backup_count: 备份文件数量
    
    返回:
        根 logger
    
    使用示例:
        logger = setup_logging(level="DEBUG", log_file="pyclaw.log")
    """
    # 创建根 logger
    root_logger = logging.getLogger("pyclaw")
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # 清除已有处理器
    root_logger.handlers.clear()
    
    # 创建格式化器
    if use_structured:
        # 结构化日志（JSON）
        formatter = StructuredFormatter()
    else:
        # 普通日志
        format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        
        if use_color and sys.stdout.isatty():
            formatter = ColoredFormatter(format_str, datefmt=date_format)
        else:
            formatter = logging.Formatter(format_str, datefmt=date_format)
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 文件处理器（带轮转）
    if log_file:
        log_path = Path(log_file).expanduser()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 按大小轮转
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # 按时间轮转（每天）
        # time_handler = TimedRotatingFileHandler(
        #     log_path,
        #     when='D',
        #     interval=1,
        #     backupCount=backup_count,
        #     encoding='utf-8'
        # )
        # time_handler.setFormatter(formatter)
        # root_logger.addHandler(time_handler)
    
    # 记录启动信息
    root_logger.info(f"日志系统已初始化 (级别：{level})")
    
    if log_file:
        root_logger.info(f"日志文件：{log_file}")
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    获取子 logger
    
    参数:
        name: logger 名称（通常是模块名）
    
    返回:
        logger 实例
    
    使用示例:
        logger = get_logger(__name__)
    """
    return logging.getLogger(f"pyclaw.{name}")


def log_with_extra(
    logger: logging.Logger,
    level: str,
    message: str,
    **extra_data,
):
    """
    记录带额外数据的日志
    
    参数:
        logger: logger 实例
        level: 日志级别
        message: 日志消息
        **extra_data: 额外数据
    
    使用示例:
        log_with_extra(logger, "INFO", "用户登录", user_id=123, ip="192.168.1.1")
    """
    record = logger.makeRecord(
        logger.name,
        getattr(logging, level.upper()),
        "",
        0,
        message,
        (),
        None
    )
    record.extra_data = extra_data
    logger.handle(record)


# ============================================================================
# 日志级别快捷函数
# ============================================================================

def debug(logger: logging.Logger, message: str, **kwargs):
    """记录 DEBUG 日志"""
    log_with_extra(logger, "DEBUG", message, **kwargs)


def info(logger: logging.Logger, message: str, **kwargs):
    """记录 INFO 日志"""
    log_with_extra(logger, "INFO", message, **kwargs)


def warning(logger: logging.Logger, message: str, **kwargs):
    """记录 WARNING 日志"""
    log_with_extra(logger, "WARNING", message, **kwargs)


def error(logger: logging.Logger, message: str, **kwargs):
    """记录 ERROR 日志"""
    log_with_extra(logger, "ERROR", message, **kwargs)


def critical(logger: logging.Logger, message: str, **kwargs):
    """记录 CRITICAL 日志"""
    log_with_extra(logger, "CRITICAL", message, **kwargs)


# ============================================================================
# 日志上下文管理器
# ============================================================================

class log_context:
    """
    日志上下文管理器
    
    自动记录函数执行的开始、结束和耗时
    
    使用示例:
        with log_context(logger, "执行任务"):
            # 执行代码
            pass
    """
    
    def __init__(self, logger: logging.Logger, operation: str, level: str = "INFO"):
        self.logger = logger
        self.operation = operation
        self.level = level
        self.start_time = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        self.logger.info(f"{self.operation} - 开始")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        elapsed = time.time() - self.start_time
        
        if exc_type is not None:
            self.logger.error(f"{self.operation} - 失败 (耗时：{elapsed:.2f}s): {exc_val}")
        else:
            getattr(self.logger, self.level.lower())(
                f"{self.operation} - 完成 (耗时：{elapsed:.2f}s)"
            )
        
        return False  # 不抑制异常
