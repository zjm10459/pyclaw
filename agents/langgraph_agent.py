#!/usr/bin/env python3
"""
基于 LangGraph 的 Agent 编排系统
=================================

使用 LangChain/LangGraph 最新版本 (2025-2026) 重新设计的 Agent 编排系统。

核心架构：
    用户消息 → Agent 决策 → 工具调用 → 结果处理 → 再次决策 → ... → 任务完成 → 回复用户

特点：
- 基于 LangGraph StateGraph 构建状态机
- Agent 自主决定是否调用工具
- 循环执行直到任务完成
- 支持多轮工具调用
- 持久化会话状态
- 支持人工介入 (human-in-the-loop)

参考：
- LangGraph: https://python.langchain.com/docs/langgraph/
- LangChain Agents: https://python.langchain.com/docs/langchain/agents/
- Deep Agents: https://python.langchain.com/docs/deepagents/overview/
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Literal, Annotated, TypedDict
from dataclasses import dataclass, field
from datetime import datetime
import operator

# LangChain Core 导入
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
    BaseMessage,
    messages_from_dict,
    messages_to_dict,
)
from langchain_core.tools import StructuredTool, tool

# LangGraph 导入
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState

# 本地导入
from tools.registry import ToolRegistry

logger = logging.getLogger("pyclaw.langgraph_agent")


# ============================================================================
# 状态定义
# ============================================================================

class AgentState(TypedDict):
    """
    LangGraph Agent 状态
    
    使用 TypedDict 定义，LangGraph 会自动管理消息累加。
    
    属性:
        messages: 消息列表 (自动累加)
        system_prompt: 系统提示词
        max_iterations: 最大迭代次数
        current_iteration: 当前迭代次数
        task_complete: 任务是否完成
    """
    messages: Annotated[List[BaseMessage], add_messages]
    system_prompt: str
    max_iterations: int
    current_iteration: int
    task_complete: bool


# ============================================================================
# Agent 配置
# ============================================================================

@dataclass
class LangGraphAgentConfig:
    """
    Agent 配置
    
    属性:
        name: Agent 名称
        model: 模型名称 (支持 "provider:model" 格式)
        temperature: 温度参数
        max_tokens: 最大输出 token 数
        system_prompt: 系统提示词
        max_iterations: 最大迭代次数 (防止无限循环)
        interrupt_before_tools: 是否在工具执行前中断 (用于人工审核)
    """
    name: str = "assistant"
    model: str = "qwen3.5-plus"
    provider: str = "bailian"
    temperature: float = 0.7
    max_tokens: int = 4096
    system_prompt: str = "你是一个全能的 AI 助手。"
    max_iterations: int = 10
    interrupt_before_tools: bool = False  # 是否在工具执行前中断


# ============================================================================
# LangGraph Agent 主类
# ============================================================================

class LangGraphAgent:
    """
    基于 LangGraph 的 Agent 编排系统
    
    核心流程：
        1. 接收用户消息
        2. Agent 决定是否调用工具
        3. 如果需要，执行工具
        4. 返回 Agent 继续处理
        5. 循环直到任务完成
        6. 回复用户
    
    架构图:
        START → agent_node → should_continue?
                              ↓
                         [需要工具] → tool_node → agent_node (循环)
                              ↓
                         [任务完成] → END
    """

    def __init__(
            self,
            config: Optional[LangGraphAgentConfig] = None,
            tool_registry: Optional[ToolRegistry] = None,
            workspace_path: Optional[str] = None,
            skill_loader: Optional[Any] = None,
            rag_memory: Optional[Any] = None,
    ):
        """
        初始化 LangGraph Agent
        
        参数:
            config: Agent 配置
            tool_registry: 工具注册表
            workspace_path: 工作区路径 (用于加载人格记忆等文件)
            skill_loader: 技能加载器 (用于注入技能说明)
            rag_memory: RAG 记忆系统 (用于长期记忆检索)
        """
        self.config = config or LangGraphAgentConfig()
        self.tool_registry = tool_registry or ToolRegistry()
        self.workspace_path = workspace_path
        self.skill_loader = skill_loader
        self.rag_memory = rag_memory

        # LangChain 组件
        self.llm = None
        self.llm_with_tools = None
        self.tools = []

        # LangGraph 组件
        self.graph = None
        self.memory = MemorySaver()  # 持久化记忆

        # 初始化
        self._init_llm()
        self._init_tools()
        self._init_graph()

        logger.info(f"LangGraph Agent 初始化完成：{self.config.name}")
        if self.skill_loader:
            logger.info(f"技能加载器：已注入")
        if self.rag_memory:
            logger.info(f"RAG 记忆：已注入")

    def _init_llm(self):
        """
        初始化 LLM
        
        使用 LangChain 1.2+ 的 init_chat_model。
        """
        try:
            from langchain.chat_models import init_chat_model

            # 构建模型标识符
            model_identifier = f"{self.config.provider}:{self.config.model}"

            self.llm = init_chat_model(
                model_identifier,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

            logger.info(f"LLM 初始化成功：{model_identifier}")

        except Exception as e:
            logger.warning(f"LLM 初始化失败 ({e})，尝试回退方案...")
            self._init_llm_fallback()

    def _init_llm_fallback(self):
        """LLM 初始化回退方案"""
        try:
            import os
            import json
            from pathlib import Path
            from langchain_openai import ChatOpenAI
            # 加载配置文件
            provider_config = self._load_provider_config()

            if self.config.provider == "bailian":
                # 从配置文件或环境变量获取 API 配置
                api_base = provider_config.get("bailian", {}).get("base_url",
                                                                  "https://dashscope.aliyuncs.com/compatible-mode/v1")
                api_key = provider_config.get("bailian", {}).get("api_key",
                                                                 os.getenv("DASHSCOPE_API_KEY", "sk-default"))

                # 处理环境变量占位符
                if api_key.startswith("${") and api_key.endswith("}"):
                    env_var_name = api_key[2:-1]
                    api_key = os.getenv(env_var_name, "sk-default")

                self.llm = ChatOpenAI(
                    model=self.config.model,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    base_url=api_base,
                    api_key=api_key,
                )
                logger.info(f"LLM 初始化成功 (通义千问): {self.config.model}")

            elif self.config.provider == "openai":
                api_base = provider_config.get("openai", {}).get("base_url",
                                                                 "https://api.openai.com/v1")
                api_key = provider_config.get("openai", {}).get("api_key",
                                                                os.getenv("OPENAI_API_KEY", ""))

                if api_key.startswith("${") and api_key.endswith("}"):
                    env_var_name = api_key[2:-1]
                    api_key = os.getenv(env_var_name, "")

                self.llm = ChatOpenAI(
                    model=self.config.model,
                    temperature=self.config.temperature,
                    base_url=api_base,
                    api_key=api_key,
                )
                logger.info(f"LLM 初始化成功 (OpenAI): {self.config.model}")

            elif self.config.provider == "anthropic":
                # Anthropic - 使用 langchain-anthropic (推荐)
                try:
                    from langchain_anthropic import ChatAnthropic
                except ImportError:
                    logger.warning("langchain-anthropic 未安装，回退到 langchain_community")
                    from langchain_community.chat_models import ChatAnthropic

                api_key = provider_config.get("anthropic", {}).get("api_key",
                                                                   os.getenv("ANTHROPIC_API_KEY", ""))

                if api_key.startswith("${") and api_key.endswith("}"):
                    env_var_name = api_key[2:-1]
                    api_key = os.getenv(env_var_name, "")

                self.llm = ChatAnthropic(
                    model=self.config.model,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    anthropic_api_key=api_key,
                )
                logger.info(f"LLM 初始化成功 (Anthropic): {self.config.model}")

            else:
                # 默认使用 langchain-openai 的 ChatOpenAI
                try:
                    from langchain_openai import ChatOpenAI
                except ImportError:
                    logger.warning("langchain-openai 未安装，回退到 langchain_community")
                    from langchain_community.chat_models import ChatOpenAI

                api_key = os.getenv("OPENAI_API_KEY", "")
                self.llm = ChatOpenAI(
                    model=self.config.model if ":" not in self.config.model else "gpt-4",
                    temperature=self.config.temperature,
                    api_key=api_key,
                )
                logger.info(f"LLM 初始化成功 (默认): {self.config.model}")

            logger.info(f"LLM 初始化成功 (回退模式): {self.config.provider}/{self.config.model}")

        except Exception as e:
            logger.exception(f"LLM 初始化失败：{e}")
            raise

    def _load_provider_config(self) -> Dict[str, Any]:
        """
        加载 Provider 配置文件
        
        返回:
            Provider 配置字典
        """
        from pathlib import Path
        import json

        # 可能的配置文件路径
        config_paths = [
            Path.cwd() / "config.json",
            Path.home() / ".pyclaw" / "config.json",
            Path(__file__).parent.parent / "config.json",
        ]

        for config_path in config_paths:
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        providers = config.get("providers", {})
                        logger.debug(f"从 {config_path} 加载 Provider 配置")
                        return providers
                except Exception as e:
                    logger.warning(f"加载配置文件失败 {config_path}: {e}")

        # 如果没有配置文件，返回空字典（使用环境变量）
        logger.debug("未找到配置文件，将使用环境变量")
        return {}

    def _init_tools(self):
        """
        初始化工具
        
        将 PyClaw 工具转换为 LangChain StructuredTool 格式。
        注意：工具注册表由 main.py 初始化，这里只做转换。
        """
        langchain_tools = []

        if not self.tool_registry or not self.tool_registry.tools:
            logger.info("ℹ 未配置工具注册表，跳过工具初始化")
            self.tools = []
            return

        for tool_name, tool_def in self.tool_registry.tools.items():
            try:
                # 检查是否是 ToolDefinition 对象
                if hasattr(tool_def, 'function'):
                    # ToolDefinition 对象，使用 function 属性
                    # 从 parameters 创建 Pydantic schema
                    args_schema = None
                    if hasattr(tool_def, 'parameters') and tool_def.parameters:
                        try:
                            from pydantic import BaseModel, create_model

                            # 从 JSON Schema 创建 Pydantic model
                            params = tool_def.parameters.get('properties', {})
                            required = tool_def.parameters.get('required', [])

                            # 构建字段定义
                            field_definitions = {}
                            for param_name, param_info in params.items():
                                param_type = param_info.get('type', 'str')
                                param_desc = param_info.get('description', '')
                                default = ... if param_name in required else None

                                # 类型映射
                                type_map = {
                                    'string': str,
                                    'integer': int,
                                    'number': float,
                                    'boolean': bool,
                                    'array': list,
                                    'object': dict,
                                }
                                python_type = type_map.get(param_type, str)

                                field_definitions[param_name] = (python_type, default)

                            # 创建动态 model
                            if field_definitions:
                                args_schema = create_model(
                                    f"{tool_def.name.title()}Schema",
                                    **field_definitions,
                                    __doc__=tool_def.description,
                                )
                        except Exception as e:
                            logger.debug(f"创建 args_schema 失败 {tool_name}: {e}")

                    langchain_tool = StructuredTool(
                        name=tool_def.name,
                        description=tool_def.description,
                        func=tool_def.function,
                        args_schema=args_schema,
                    )
                elif hasattr(tool_def, '_run'):
                    # LangChain 工具对象（如 RequestsGetTool, ReadFileTool 等）
                    # 使用 _run 方法作为入口
                    langchain_tool = StructuredTool(
                        name=getattr(tool_def, 'name', tool_name),
                        description=getattr(tool_def, 'description', ''),
                        func=tool_def._run,
                        args_schema=getattr(tool_def, 'args_schema', None),
                    )
                else:
                    logger.warning(f"⚠ 未知工具类型：{tool_name}")
                    continue

                langchain_tools.append(langchain_tool)
                logger.debug(f"工具转换成功：{tool_name}")
            except Exception as e:
                logger.error(f"工具转换失败 {tool_name}: {e}")

        self.tools = langchain_tools
        logger.info(f"✓ 工具初始化完成：{len(self.tools)} 个工具 (来自 tool_registry)")

        # 创建带工具的 LLM
        if self.tools:
            self.llm_with_tools = self.llm.bind_tools(self.tools)

        logger.info(f"工具初始化完成：{len(self.tools)} 个工具")

    def _init_graph(self):
        """
        初始化 LangGraph StateGraph
        
        构建 Agent 执行图:
            START → agent_node → should_continue
                                 ↓
                          tools_node → agent_node (循环)
                                 ↓
                                END
        """
        try:
            # 创建 StateGraph
            builder = StateGraph(AgentState)

            # 添加节点
            builder.add_node("agent", self._agent_node)
            builder.add_node("tools", ToolNode(self.tools))

            # 设置入口
            builder.add_edge(START, "agent")

            # 添加条件边 (决定是否调用工具)
            builder.add_conditional_edges(
                "agent",
                self._should_continue,
                {
                    "continue": "tools",  # 需要调用工具
                    "end": END,  # 任务完成
                }
            )

            # 工具执行后返回 agent 节点 (循环)
            builder.add_edge("tools", "agent")

            # 编译图
            interrupt_before = ["tools"] if self.config.interrupt_before_tools else None
            self.graph = builder.compile(
                checkpointer=self.memory,
                interrupt_before=interrupt_before,
            )

            logger.info("LangGraph StateGraph 初始化成功")

        except Exception as e:
            logger.exception(f"LangGraph 初始化失败：{e}")
            raise

    def _agent_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Agent 节点：调用 LLM 决定是否调用工具
        
        参数:
            state: 当前状态 (包含消息历史)
        
        返回:
            更新后的状态
        """
        try:
            # 检查迭代次数
            if state["current_iteration"] >= state["max_iterations"]:
                logger.warning(f"达到最大迭代次数 ({state['max_iterations']})，强制结束")
                return {
                    "messages": [
                        AIMessage(content="已达到最大迭代次数，无法继续处理。")
                    ],
                    "task_complete": True,
                }

            # 构建系统提示词（注入 RAG 记忆）
            system_prompt = self._build_system_prompt_with_rag(state)

            # 准备消息
            messages = [
                SystemMessage(content=system_prompt),
                *state["messages"]
            ]

            # 调用 LLM (带工具)
            if self.tools and self.llm_with_tools:
                response = self.llm_with_tools.invoke(messages)
            else:
                response = self.llm.invoke(messages)

            # 更新迭代次数
            new_iteration = state["current_iteration"] + 1

            # 检查是否有工具调用
            if hasattr(response, 'tool_calls') and response.tool_calls:
                logger.info(f"Agent 决定调用工具：{[tc['name'] for tc in response.tool_calls]}")
                return {
                    "messages": [response],
                    "current_iteration": new_iteration,
                    "task_complete": False,
                }
            else:
                # 没有工具调用，任务完成
                logger.info("Agent 完成任务，准备回复用户")
                return {
                    "messages": [response],
                    "current_iteration": new_iteration,
                    "task_complete": True,
                }

        except Exception as e:
            logger.exception(f"Agent 节点执行失败：{e}")
            return {
                "messages": [
                    AIMessage(content=f"错误：{str(e)}")
                ],
                "task_complete": True,
            }

    def _should_continue(self, state: AgentState) -> Literal["continue", "end"]:
        """
        判断是否继续执行 (调用工具还是结束)
        
        检查最后一条消息是否有工具调用。
        
        参数:
            state: 当前状态
        
        返回:
            "continue" 或 "end"
        """
        messages = state["messages"]

        if not messages:
            return "end"

        last_message = messages[-1]

        # 如果是 AI 消息且有工具调用
        if isinstance(last_message, AIMessage):
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                return "continue"

        # 如果任务已完成
        if state.get("task_complete", False):
            return "end"

        return "end"

    def _build_system_prompt(self, state: AgentState) -> str:
        """
        构建系统提示词 (注入工作区文件 + 技能说明)
        
        参数:
            state: 当前状态
        
        返回:
            系统提示词
        """
        from pathlib import Path

        base_prompt = self.config.system_prompt

        # 加载工作区文件
        workspace_files = self._load_workspace_files()

        parts = [base_prompt]

        if workspace_files:
            if "system_prompt" in workspace_files:
                parts.append("\n\n## 人格记忆\n\n" + workspace_files["system_prompt"])

            if "user_context" in workspace_files:
                parts.append("\n\n## 用户信息\n\n" + workspace_files["user_context"])

            if "workspace_context" in workspace_files:
                parts.append("\n\n## 工作区说明\n\n" + workspace_files["workspace_context"])

        # 注入技能说明（SKILL.md instructions）
        if self.skill_loader:
            try:
                skills_prompt = self.skill_loader.get_skills_prompt()
                if skills_prompt:
                    parts.append("\n\n## Available Skills\n\n" + skills_prompt)
                    logger.debug(f"注入技能说明：{len(skills_prompt)} 字符")
            except Exception as e:
                logger.warning(f"获取技能说明失败：{e}")

        # 添加工具说明
        if self.tools:
            tools_info = "\n\n## 可用工具\n\n你可以使用以下工具来帮助用户：\n"
            for tool in self.tools:
                tools_info += f"- {tool.name}: {tool.description}\n"
            parts.append(tools_info)

        return "\n".join(parts)

    def _build_system_prompt_with_rag(self, state: AgentState) -> str:
        """
        构建系统提示词（注入 RAG 记忆 + 今日对话上下文）
        
        采用混合策略：
        1. LangGraph MemorySaver - 当前会话历史（自动）
        2. 长期记忆.md - 用户偏好和背景
        3. 今日 JSON - 最近对话摘要（跨会话连续性）
        
        参数:
            state: 当前状态
        
        返回:
            系统提示词（包含完整上下文）
        """
        # 1. 基础系统提示词
        base_prompt = self._build_system_prompt(state)

        # 2. 长期记忆（全部加载）
        try:
            from tools.memory_tools import get_memory_file
            from pathlib import Path

            memory_file = get_memory_file()
            if memory_file.exists():
                content = memory_file.read_text(encoding="utf-8")

                # 提取所有记忆内容（去掉标题和说明）
                lines = content.split("\n")
                memory_entries = []
                in_entry = False

                for line in lines:
                    if line.startswith("## 📅") or line.startswith("### "):
                        memory_entries.append(line)
                        in_entry = True
                    elif in_entry and line.strip() and not line.startswith("---"):
                        memory_entries.append(line)

                if memory_entries:
                    long_term_memory = "\n".join(memory_entries[:50])  # 限制最多 50 行
                    base_prompt += f"\n\n## 🧠 长期记忆（全部）\n\n{long_term_memory}"
                    logger.debug(f"注入长期记忆：{len(memory_entries)} 条")

        except Exception as e:
            logger.debug(f"加载长期记忆失败：{e}")

        # 3. 今日对话上下文（跨会话连续性）
        try:
            from tools.chat_recorder import get_today_records

            # 获取今日最近 2 次对话
            records_result = get_today_records(limit=2)

            if records_result.get("success") and records_result.get("records"):
                records = records_result["records"]

                # 生成今日对话摘要
                today_context = "\n\n## 📅 今日对话摘要\n\n"
                today_context += "以下是用户今天的最近对话，帮助保持上下文连续性：\n\n"

                for i, record in enumerate(records, 1):
                    timestamp = record.get("timestamp", "")
                    summary = record.get("summary", "")
                    msg_count = record.get("message_count", 0)

                    today_context += f"{i}. **{timestamp}** - {summary} ({msg_count}条消息)\n"

                    # 提取关键信息（用户最后的问题）
                    if record.get("messages"):
                        last_msg = record["messages"][-1]
                        if last_msg.get("role") in ["human", "user"]:
                            today_context += f"   → 用户：{last_msg['content'][:100]}...\n"

                today_context += "\n如果用户提到'刚才'、'之前'等词，参考以上对话。\n"
                base_prompt += today_context
                logger.debug(f"注入今日对话上下文：{len(records)} 条记录")

        except Exception as e:
            logger.debug(f"获取今日对话失败：{e}")

        return base_prompt

        # 添加执行说明
        parts.append("""
## 执行流程

1. 分析用户需求
2. 如果需要，调用工具获取信息或执行操作
3. 根据工具结果继续处理或再次调用工具
4. 循环执行直到任务完成
5. 回复用户

注意：
- 你可以多次调用工具
- 每次调用工具后，你会看到工具的执行结果
- 根据结果决定下一步行动
- 当任务完成时，直接回复用户
""")

        return "\n".join(parts)

    def _load_workspace_files(self) -> Dict[str, str]:
        """加载工作区文件"""
        from pathlib import Path

        workspace_files = {}

        if not self.workspace_path:
            workspace_path = Path.home() / ".pyclaw" / "workspace"
        else:
            workspace_path = Path(self.workspace_path)

        # 必须加载的文件
        required_files = [
            ("人格记忆.md", "system_prompt"),
            ("AGENT.md", "workspace_context"),
            ("USER.md", "user_context"),
        ]

        for filename, key in required_files:
            filepath = workspace_path / filename
            if filepath.exists():
                try:
                    content = filepath.read_text(encoding='utf-8')
                    workspace_files[key] = content
                except Exception as e:
                    logger.warning(f"加载 {filename} 失败：{e}")

        return workspace_files

    async def run(
            self,
            input_text: str,
            session_key: str = "default",
            stream: bool = False,
    ) -> Dict[str, Any]:
        """
        运行 Agent
        
        参数:
            input_text: 用户输入
            session_key: 会话键 (用于隔离不同会话)
            stream: 是否流式输出
        
        返回:
            执行结果
        """
        logger.info(f"运行 Agent: {input_text[:50]}...")

        try:
            # 准备初始状态
            initial_state = AgentState(
                messages=[HumanMessage(content=input_text)],
                system_prompt=self.config.system_prompt,
                max_iterations=self.config.max_iterations,
                current_iteration=0,
                task_complete=False,
            )

            # 执行图
            if stream:
                return await self._run_stream(initial_state, session_key)
            else:
                return await self._run_normal(initial_state, session_key)

        except Exception as e:
            logger.exception(f"Agent 执行失败：{e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def _run_normal(
            self,
            initial_state: AgentState,
            session_key: str,
    ) -> Dict[str, Any]:
        """普通模式执行"""
        loop = asyncio.get_event_loop()

        # 在线程池中执行
        result = await loop.run_in_executor(
            None,
            lambda: list(self.graph.stream(
                initial_state,
                config={"configurable": {"thread_id": session_key}},
            ))
        )

        # 提取最终输出
        all_messages = []
        for step in result:
            for node_name, node_output in step.items():
                if "messages" in node_output:
                    all_messages.extend(node_output["messages"])

        # 获取最后的 AI 回复
        output = ""
        tool_calls_count = 0
        for msg in reversed(all_messages):
            if isinstance(msg, AIMessage):
                output = msg.content
                break

        # 统计工具调用次数
        for msg in all_messages:
            if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                tool_calls_count += len(msg.tool_calls)

        logger.info(f"Agent 执行完成：{len(output)} 字符，工具调用 {tool_calls_count} 次")

        # ========== 自动保存聊天记录 ==========
        try:
            from tools.chat_recorder import save_chat_record

            # 转换消息格式
            chat_messages = []
            first_user_msg = ""
            last_user_msg = ""

            for msg in all_messages:
                msg_dict = {
                    "role": msg.type if hasattr(msg, 'type') else "unknown",
                    "content": msg.content if hasattr(msg, 'content') else str(msg),
                }
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    msg_dict["tool_calls"] = msg.tool_calls
                chat_messages.append(msg_dict)

                # 提取用户消息用于摘要
                if isinstance(msg, HumanMessage) and hasattr(msg, 'content'):
                    if not first_user_msg:
                        first_user_msg = msg.content[:100]
                    last_user_msg = msg.content[:100]

            # 生成详细摘要（包含主题、工具、关键信息）
            user_msgs = [m for m in all_messages if isinstance(m, HumanMessage)]
            ai_msgs = [m for m in all_messages if isinstance(m, AIMessage)]
            tool_msgs = [m for m in all_messages if hasattr(m, 'type') and m.type == "tool"]

            # 1. 提取用户主要意图
            user_intent = ""
            if user_msgs:
                user_intent = user_msgs[0].content[:80] if hasattr(user_msgs[0], 'content') else ""

            # 2. 检测工具调用及结果
            tool_info = ""
            tool_results = []
            for msg in ai_msgs:
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tc in msg.tool_calls:
                        tool_name = tc.get('name', 'unknown')
                        tool_args = tc.get('args', {})
                        tool_info = f"使用 {tool_name}"

                        # 提取工具参数作为关键词
                        if 'query' in tool_args:
                            tool_results.append(f"搜索：{str(tool_args['query'])[:50]}")
                        elif 'url' in tool_args:
                            tool_results.append(f"访问：{tool_args['url'][:50]}")

            # 3. 提取工具返回结果
            tool_output_summary = ""
            for msg in tool_msgs:
                if hasattr(msg, 'content') and msg.content:
                    content = msg.content[:100]
                    # 提取关键信息
                    if "搜索" in tool_info.lower() or "search" in tool_info.lower():
                        tool_output_summary = f"找到相关信息"
                    elif len(content) > 50:
                        tool_output_summary = f"获取内容 ({len(content)} 字)"
                    else:
                        tool_output_summary = f"获取结果"

            # 4. 提取 AI 最终回复的关键信息
            ai_summary = ""
            if ai_msgs:
                last_ai_msg = ai_msgs[-1]
                if hasattr(last_ai_msg, 'content') and last_ai_msg.content:
                    content = last_ai_msg.content
                    # 提取第一句有意义的话
                    for sentence in content.split('。'):
                        if len(sentence.strip()) > 10:
                            ai_summary = sentence.strip()[:60]
                            break

            # 5. 组合详细摘要
            summary_parts = []
            if user_intent:
                summary_parts.append(f"用户：{user_intent}")
            if tool_info:
                summary_parts.append(tool_info)
            if tool_results:
                summary_parts.extend(tool_results)
            if tool_output_summary:
                summary_parts.append(tool_output_summary)
            if ai_summary:
                summary_parts.append(f"回复：{ai_summary}")

            # 生成最终摘要
            if summary_parts:
                summary = " | ".join(summary_parts)
            else:
                summary = f"对话记录：{len(all_messages)} 条消息"

            # 限制摘要长度
            if len(summary) > 300:
                summary = summary[:297] + "..."

            # 保存记录
            save_chat_record(
                messages=chat_messages,
                session_key=session_key,
                summary=summary,
            )
        except Exception as e:
            logger.debug(f"保存聊天记录失败：{e}")

        return {
            "success": True,
            "output": output,
            "session_key": session_key,
            "tool_calls_count": tool_calls_count,
            "full_messages": messages_to_dict(all_messages),
            "iterations": len(result),
        }

    async def _run_stream(
            self,
            initial_state: AgentState,
            session_key: str,
    ) -> Dict[str, Any]:
        """流式模式执行"""
        # TODO: 实现流式输出
        return await self._run_normal(initial_state, session_key)

    def run_sync(
            self,
            input_text: str,
            session_key: str = "default",
            stream: bool = False,
    ) -> Dict[str, Any]:
        """
        同步版本 run 方法（用于在多 Agent 系统中调用）
        
        参数:
            input_text: 用户输入
            session_key: 会话键
            stream: 是否流式输出
        
        返回:
            执行结果
        """
        import asyncio

        # 使用 asyncio.run 在新的循环中运行
        return asyncio.run(
            self.run(input_text=input_text, session_key=session_key, stream=stream)
        )


# ============================================================================
# 便捷函数
# ============================================================================

def create_langgraph_agent(
        model: str = "qwen3.5-plus",
        provider: str = "bailian",
        tools: Optional[List] = None,
        system_prompt: str = "你是一个有帮助的 AI 助手。",
        max_iterations: int = 10,
        workspace_path: Optional[str] = None,
) -> LangGraphAgent:
    """
    创建 LangGraph Agent 的便捷函数
    
    参数:
        model: 模型名称
        provider: Provider 名称
        tools: 工具列表
        system_prompt: 系统提示词
        max_iterations: 最大迭代次数
        workspace_path: 工作区路径
    
    返回:
        LangGraphAgent 实例
    """
    config = LangGraphAgentConfig(
        model=model,
        provider=provider,
        system_prompt=system_prompt,
        max_iterations=max_iterations,
    )

    # 创建工具注册表
    tool_registry = ToolRegistry()
    if tools:
        for tool in tools:
            tool_registry.register_tool(tool)

    return LangGraphAgent(
        config=config,
        tool_registry=tool_registry,
        workspace_path=workspace_path,
    )


# ============================================================================
# 测试入口
# ============================================================================

if __name__ == "__main__":
    import sys
    from pathlib import Path

    # 添加路径
    sys.path.insert(0, str(Path(__file__).parent.parent))

    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )

    # 创建 Agent
    agent = create_langgraph_agent(
        model="qwen3.5-plus",
        provider="bailian",
        system_prompt="你是一个有帮助的 AI 助手，使用中文回复。",
        workspace_path=str(Path.home() / ".pyclaw" / "workspace"),
    )


    # 测试运行
    async def test():
        result = await agent.run(
            input_text="你好，请介绍一下你自己。",
            session_key="test_session",
        )
        print(f"\n结果：{result['output']}\n")
        print(f"工具调用次数：{result.get('tool_calls_count', 0)}")
        print(f"迭代次数：{result.get('iterations', 0)}")


    asyncio.run(test())
