"""
渠道适配器模块
==============

提供不同消息渠道的适配器实现。

已支持渠道:
- Feishu (飞书)
"""

from .feishu_channel import FeishuChannel, FeishuConfig

__all__ = [
    "FeishuChannel",
    "FeishuConfig",
]
