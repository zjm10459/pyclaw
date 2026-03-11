"""
LLM Provider 集成
=================

实现多种 LLM Provider 的调用接口。

支持的 Provider:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Ollama (本地模型)
- 模型故障转移

使用示例:
    from agents.providers import get_provider
    
    provider = get_provider("openai")
    response = provider.chat("你好")
"""

import os
import logging
from typing import Dict, Any, Optional, List, Iterator
from abc import ABC, abstractmethod
from dataclasses import dataclass

logger = logging.getLogger("pyclaw.providers")


@dataclass
class ChatMessage:
    """聊天消息"""
    role: str  # system/user/assistant
    content: str


@dataclass
class ChatResponse:
    """聊天响应"""
    content: str
    model: str
    usage: Dict[str, int]
    raw_response: Any = None


class BaseProvider(ABC):
    """Provider 基类"""
    
    def __init__(self, api_key: str = "", base_url: str = ""):
        self.api_key = api_key
        self.base_url = base_url
    
    @abstractmethod
    def chat(self, messages: List[ChatMessage], **kwargs) -> ChatResponse:
        """发送聊天请求"""
        pass
    
    @abstractmethod
    def chat_stream(self, messages: List[ChatMessage], **kwargs) -> Iterator[str]:
        """流式聊天"""
        pass


class OpenAIProvider(BaseProvider):
    """OpenAI Provider"""
    
    def __init__(self, api_key: str = "", base_url: str = ""):
        super().__init__(
            api_key=api_key or os.environ.get("OPENAI_API_KEY", ""),
            base_url=base_url or "https://api.openai.com/v1",
        )
    
    def chat(self, messages: List[ChatMessage], **kwargs) -> ChatResponse:
        """OpenAI 聊天"""
        try:
            from openai import OpenAI
            
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
            
            # 转换消息格式
            openai_messages = [
                {"role": m.role, "content": m.content}
                for m in messages
            ]
            
            response = client.chat.completions.create(
                model=kwargs.get("model", "gpt-4"),
                messages=openai_messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 4096),
            )
            
            return ChatResponse(
                content=response.choices[0].message.content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                raw_response=response,
            )
        
        except Exception as e:
            logger.exception(f"OpenAI 调用失败：{e}")
            raise
    
    def chat_stream(self, messages: List[ChatMessage], **kwargs) -> Iterator[str]:
        """OpenAI 流式聊天"""
        from openai import OpenAI
        
        client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )
        
        openai_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]
        
        stream = client.chat.completions.create(
            model=kwargs.get("model", "gpt-4"),
            messages=openai_messages,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 4096),
            stream=True,
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class AnthropicProvider(BaseProvider):
    """Anthropic Provider"""
    
    def __init__(self, api_key: str = ""):
        super().__init__(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY", ""),
        )
    
    def chat(self, messages: List[ChatMessage], **kwargs) -> ChatResponse:
        """Anthropic 聊天"""
        try:
            from anthropic import Anthropic
            
            client = Anthropic(api_key=self.api_key)
            
            # 分离系统消息
            system_message = ""
            user_messages = []
            
            for msg in messages:
                if msg.role == "system":
                    system_message = msg.content
                else:
                    user_messages.append(msg)
            
            response = client.messages.create(
                model=kwargs.get("model", "claude-3-sonnet-20240229"),
                max_tokens=kwargs.get("max_tokens", 4096),
                system=system_message,
                messages=[
                    {"role": m.role, "content": m.content}
                    for m in user_messages
                ],
            )
            
            return ChatResponse(
                content=response.content[0].text,
                model=response.model,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                },
                raw_response=response,
            )
        
        except Exception as e:
            logger.exception(f"Anthropic 调用失败：{e}")
            raise
    
    def chat_stream(self, messages: List[ChatMessage], **kwargs) -> Iterator[str]:
        """Anthropic 流式聊天"""
        from anthropic import Anthropic
        
        client = Anthropic(api_key=self.api_key)
        
        system_message = ""
        user_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                user_messages.append(msg)
        
        with client.messages.stream(
            model=kwargs.get("model", "claude-3-sonnet-20240229"),
            max_tokens=kwargs.get("max_tokens", 4096),
            system=system_message,
            messages=[
                {"role": m.role, "content": m.content}
                for m in user_messages
            ],
        ) as stream:
            for text in stream.text_stream:
                yield text


class BailianProvider(BaseProvider):
    """阿里云百炼（通义千问）Provider"""
    
    def __init__(self, api_key: str = "", base_url: str = ""):
        super().__init__(
            api_key=api_key or os.environ.get("DASHSCOPE_API_KEY", ""),
            base_url=base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
    
    def chat(self, messages: List[ChatMessage], **kwargs) -> ChatResponse:
        """百炼（通义千问）聊天"""
        try:
            from openai import OpenAI
            
            # 百炼兼容 OpenAI API 格式
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
            
            # 转换消息格式
            openai_messages = [
                {"role": m.role, "content": m.content}
                for m in messages
            ]
            
            # 获取模型名称
            model = kwargs.get("model", "qwen-plus")
            
            # 调用 API
            response = client.chat.completions.create(
                model=model,
                messages=openai_messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2048),
            )
            
            logger.info(f"百炼 API 调用成功：{model}")
            
            return ChatResponse(
                content=response.choices[0].message.content,
                model=model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                raw_response=response,
            )
        
        except Exception as e:
            logger.exception(f"百炼调用失败：{e}")
            raise
    
    def chat_stream(self, messages: List[ChatMessage], **kwargs) -> Iterator[str]:
        """百炼流式聊天"""
        from openai import OpenAI
        
        client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )
        
        openai_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]
        
        stream = client.chat.completions.create(
            model=kwargs.get("model", "qwen-plus"),
            messages=openai_messages,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 2048),
            stream=True,
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class OllamaProvider(BaseProvider):
    """Ollama 本地模型 Provider"""
    
    def __init__(self, base_url: str = ""):
        super().__init__(
            base_url=base_url or "http://localhost:11434",
        )
    
    def chat(self, messages: List[ChatMessage], **kwargs) -> ChatResponse:
        """Ollama 聊天"""
        try:
            import requests
            
            ollama_messages = [
                {"role": m.role, "content": m.content}
                for m in messages
            ]
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": kwargs.get("model", "llama2"),
                    "messages": ollama_messages,
                    "stream": False,
                },
            )
            response.raise_for_status()
            
            data = response.json()
            
            return ChatResponse(
                content=data["message"]["content"],
                model=kwargs.get("model", "llama2"),
                usage=data.get("prompt_eval_count", 0),
                raw_response=data,
            )
        
        except Exception as e:
            logger.exception(f"Ollama 调用失败：{e}")
            raise
    
    def chat_stream(self, messages: List[ChatMessage], **kwargs) -> Iterator[str]:
        """Ollama 流式聊天"""
        import requests
        import json
        
        ollama_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]
        
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": kwargs.get("model", "llama2"),
                "messages": ollama_messages,
                "stream": True,
            },
            stream=True,
        )
        
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                if "message" in data:
                    yield data["message"].get("content", "")


class FailoverProvider(BaseProvider):
    """故障转移 Provider
    
    按顺序尝试多个 Provider，直到成功。
    """
    
    def __init__(self, providers: List[tuple]):
        """
        初始化故障转移 Provider
        
        参数:
            providers: Provider 配置列表 [(name, provider_instance, priority), ...]
        """
        self.providers = sorted(providers, key=lambda x: x[2])  # 按优先级排序
    
    def chat(self, messages: List[ChatMessage], **kwargs) -> ChatResponse:
        """带故障转移的聊天"""
        last_error = None
        
        for name, provider, _ in self.providers:
            try:
                logger.info(f"尝试使用 Provider: {name}")
                return provider.chat(messages, **kwargs)
            except Exception as e:
                logger.warning(f"Provider {name} 失败：{e}")
                last_error = e
                continue
        
        # 所有 Provider 都失败
        raise Exception(f"所有 Provider 都失败：{last_error}")
    
    def chat_stream(self, messages: List[ChatMessage], **kwargs) -> Iterator[str]:
        """带故障转移的流式聊天"""
        # 流式模式下使用第一个可用的 Provider
        for name, provider, _ in self.providers:
            try:
                yield from provider.chat_stream(messages, **kwargs)
                return
            except Exception as e:
                logger.warning(f"Provider {name} 失败：{e}")
                continue
        
        raise Exception("所有 Provider 都失败")


# Provider 工厂函数
def get_provider(name: str, **kwargs) -> BaseProvider:
    """
    获取 Provider 实例
    
    参数:
        name: Provider 名称（openai/anthropic/bailian/ollama）
        **kwargs: Provider 配置参数
    
    返回:
        Provider 实例
    """
    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "bailian": BailianProvider,  # 阿里云百炼（通义千问）
        "ollama": OllamaProvider,
    }
    
    if name not in providers:
        raise ValueError(f"未知 Provider: {name}. 支持的 Provider: {list(providers.keys())}")
    
    return providers[name](**kwargs)


def create_failover_provider() -> FailoverProvider:
    """
    创建故障转移 Provider
    
    优先级：OpenAI > Anthropic > Ollama
    
    返回:
        FailoverProvider 实例
    """
    providers = []
    
    # 尝试初始化 OpenAI
    if os.environ.get("OPENAI_API_KEY"):
        providers.append(("openai", OpenAIProvider(), 1))
    
    # 尝试初始化 Anthropic
    if os.environ.get("ANTHROPIC_API_KEY"):
        providers.append(("anthropic", AnthropicProvider(), 2))
    
    # Ollama 总是可用（本地）
    providers.append(("ollama", OllamaProvider(), 3))
    
    return FailoverProvider(providers)


# 便捷函数
def quick_chat(prompt: str, provider_name: str = "openai", **kwargs) -> str:
    """
    快速聊天
    
    参数:
        prompt: 用户输入
        provider_name: Provider 名称
        **kwargs: Provider 配置
    
    返回:
        响应文本
    """
    provider = get_provider(provider_name, **kwargs)
    
    messages = [
        ChatMessage(role="user", content=prompt),
    ]
    
    response = provider.chat(messages)
    return response.content
