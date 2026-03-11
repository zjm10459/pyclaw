#!/usr/bin/env python3
"""
多 Agent 协作系统
=================

基于 LangGraph 实现多 Agent 协作，支持：
- 角色分工（主管、专家、执行者等）
- 任务分解和分配
- Agent 间通信
- 结果汇总

架构：
    用户请求 → 主管 Agent → 任务分解 → 分配给专家 Agent → 汇总结果 → 回复用户
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Literal
from dataclasses import dataclass, field
from enum import Enum
import json

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    BaseMessage,
)

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing import Annotated, TypedDict

# 本地导入
from agents.langgraph_agent import LangGraphAgent, LangGraphAgentConfig

logger = logging.getLogger("pyclaw.multi_agent")


# ============================================================================
# Agent 角色定义
# ============================================================================

class AgentRole(str, Enum):
    """Agent 角色类型"""
    SUPERVISOR = "supervisor"  # 主管 - 负责任务分解和协调
    RESEARCHER = "researcher"  # 研究员 - 负责信息收集和研究
    CODER = "coder"  # 程序员 - 负责代码编写
    WRITER = "writer"  # 作家 - 负责文案写作
    ANALYST = "analyst"  # 分析师 - 负责数据分析
    EXECUTOR = "executor"  # 执行者 - 负责任务执行


# ============================================================================
# 状态定义
# ============================================================================

class MultiAgentState(TypedDict):
    """
    多 Agent 协作状态
    
    属性:
        messages: 消息列表
        task: 当前任务
        subtasks: 子任务列表
        current_subtask: 当前子任务索引
        agent_results: 各 Agent 的执行结果
        final_result: 最终汇总结果
        task_complete: 任务是否完成
    """
    messages: Annotated[List[BaseMessage], add_messages]
    task: str
    subtasks: List[Dict[str, Any]]
    current_subtask: int
    agent_results: Dict[str, Any]
    final_result: str
    task_complete: bool


# ============================================================================
# Agent 配置
# ============================================================================

@dataclass
class AgentDefinition:
    """
    Agent 定义
    
    属性:
        role: Agent 角色
        name: Agent 名称
        description: Agent 描述
        system_prompt: 系统提示词
        model: 模型名称
        max_iterations: 最大迭代次数
    """
    role: AgentRole
    name: str
    description: str
    system_prompt: str
    model: str = "qwen3.5-plus"
    max_iterations: int = 10


# ============================================================================
# 预定义 Agent 角色
# ============================================================================

DEFAULT_AGENTS = {
    AgentRole.SUPERVISOR: AgentDefinition(
        role=AgentRole.SUPERVISOR,
        name="主管",
        description="负责任务分解、协调和结果汇总",
        system_prompt="""你是一个主管 Agent，负责：
1. 分析用户请求，分解为可执行的子任务
2. 将子任务分配给合适的专家 Agent
3. 汇总各 Agent 的结果，生成最终回复

你的输出格式：
- 如果需要分解任务：{"action": "decompose", "subtasks": [{"role": "researcher", "task": "..."}, ...]}
- 如果需要汇总结果：{"action": "summarize", "results": {...}}
- 如果直接回复：{"action": "reply", "content": "..."}
""",
        model="qwen3.5-plus",
        max_iterations=5,
    ),
    
    AgentRole.RESEARCHER: AgentDefinition(
        role=AgentRole.RESEARCHER,
        name="研究员",
        description="负责信息收集、网络搜索、资料整理",
        system_prompt="""你是一个研究员 Agent，负责：
1. 收集与任务相关的信息
2. 进行网络搜索（如果有搜索工具）
3. 整理和总结收集到的信息

你需要详细、准确地收集信息，并注明信息来源。
""",
        model="qwen3.5-plus",
        max_iterations=10,
    ),
    
    AgentRole.CODER: AgentDefinition(
        role=AgentRole.CODER,
        name="程序员",
        description="负责代码编写、调试、审查",
        system_prompt="""你是一个程序员 Agent，负责：
1. 根据需求编写代码
2. 调试和修复代码问题
3. 进行代码审查

你需要编写清晰、高效、可维护的代码，并添加必要的注释。
""",
        model="qwen3.5-plus",
        max_iterations=10,
    ),
    
    AgentRole.WRITER: AgentDefinition(
        role=AgentRole.WRITER,
        name="作家",
        description="负责文案写作、内容创作、编辑润色",
        system_prompt="""你是一个作家 Agent，负责：
1. 撰写各类文案（邮件、报告、文章等）
2. 编辑和润色内容
3. 确保内容准确、流畅、专业

你需要根据目标受众调整写作风格，确保内容质量。
""",
        model="qwen3.5-plus",
        max_iterations=8,
    ),
    
    AgentRole.ANALYST: AgentDefinition(
        role=AgentRole.ANALYST,
        name="分析师",
        description="负责数据分析、图表生成、洞察提取",
        system_prompt="""你是一个分析师 Agent，负责：
1. 分析数据和信息
2. 提取关键洞察
3. 生成数据总结和建议

你需要用数据说话，提供有根据的分析和建议。
""",
        model="qwen3.5-plus",
        max_iterations=10,
    ),
    
    AgentRole.EXECUTOR: AgentDefinition(
        role=AgentRole.EXECUTOR,
        name="执行者",
        description="负责任务执行、工具调用、结果反馈",
        system_prompt="""你是一个执行者 Agent，负责：
1. 执行具体任务
2. 调用必要的工具
3. 反馈执行结果

你需要准确执行任务，并及时反馈进度和结果。
""",
        model="qwen3.5-plus",
        max_iterations=10,
    ),
}


# ============================================================================
# 多 Agent 协作系统
# ============================================================================

class MultiAgentCollaboration:
    """
    多 Agent 协作系统
    
    核心流程：
        1. 接收用户请求
        2. 主管 Agent 分析并分解任务
        3. 分配子任务给专家 Agent
        4. 专家 Agent 并行/串行执行
        5. 主管 Agent 汇总结果
        6. 回复用户
    """
    
    def __init__(
        self,
        agent_definitions: Optional[Dict[AgentRole, AgentDefinition]] = None,
        tool_registry: Optional[Any] = None,
        workspace_path: Optional[str] = None,
    ):
        """
        初始化多 Agent 协作系统
        
        参数:
            agent_definitions: Agent 定义字典
            tool_registry: 工具注册表
            workspace_path: 工作区路径
        """
        self.agent_definitions = agent_definitions or DEFAULT_AGENTS
        self.tool_registry = tool_registry
        self.workspace_path = workspace_path
        
        # Agent 实例缓存
        self.agents: Dict[AgentRole, LangGraphAgent] = {}
        
        # 初始化 Agent
        self._init_agents()
        
        # 构建协作图
        self.graph = None
        self._init_graph()
        
        logger.info(f"多 Agent 协作系统初始化完成：{len(self.agents)} 个 Agent")
    
    def _init_agents(self):
        """初始化所有 Agent 实例"""
        for role, definition in self.agent_definitions.items():
            try:
                config = LangGraphAgentConfig(
                    name=definition.name,
                    model=definition.model,
                    provider="bailian",  # 默认使用通义千问
                    system_prompt=definition.system_prompt,
                    max_iterations=definition.max_iterations,
                )
                
                agent = LangGraphAgent(
                    config=config,
                    tool_registry=self.tool_registry,
                    workspace_path=self.workspace_path,
                )
                
                self.agents[role] = agent
                logger.debug(f"Agent 初始化成功：{role.value}")
            
            except Exception as e:
                logger.error(f"Agent 初始化失败 {role.value}: {e}")
    
    def _init_graph(self):
        """
        初始化多 Agent 协作图
        
        架构：
            START → supervisor → route_task
            route_task → expert_agent → supervisor (循环)
            route_task → END (任务完成)
        """
        try:
            builder = StateGraph(MultiAgentState)
            
            # 添加主管节点
            builder.add_node("supervisor", self._supervisor_node)
            
            # 添加专家节点
            for role in self.agent_definitions.keys():
                if role != AgentRole.SUPERVISOR:
                    builder.add_node(
                        f"expert_{role.value}",
                        lambda state, r=role: self._expert_node(state, r),
                    )
            
            # 设置入口
            builder.add_edge(START, "supervisor")
            
            # 添加条件路由
            builder.add_conditional_edges(
                "supervisor",
                self._route_task,
                {
                    **{f"expert_{role.value}": f"expert_{role.value}" for role in self.agent_definitions if role != AgentRole.SUPERVISOR},
                    "end": END,
                }
            )
            
            # 专家执行后返回主管
            for role in self.agent_definitions.keys():
                if role != AgentRole.SUPERVISOR:
                    builder.add_edge(f"expert_{role.value}", "supervisor")
            
            # 编译图
            self.graph = builder.compile()
            
            logger.info("多 Agent 协作图初始化成功")
        
        except Exception as e:
            logger.exception(f"协作图初始化失败：{e}")
            raise
    
    def _supervisor_node(self, state: MultiAgentState) -> Dict[str, Any]:
        """
        主管节点：分析任务、分解任务、汇总结果
        
        参数:
            state: 当前状态
        
        返回:
            更新后的状态
        """
        try:
            logger.info("主管 Agent 分析任务...")
            
            # 获取主管 Agent
            supervisor = self.agents[AgentRole.SUPERVISOR]
            
            # 构建提示词
            task = state["task"]
            subtasks = state.get("subtasks", [])
            agent_results = state.get("agent_results", {})
            
            if not subtasks:
                # 首次分析，分解任务
                prompt = f"""请分析以下用户请求，并决定如何处理：

用户请求：{task}

你可以：
1. 分解为子任务并分配给专家
2. 直接回复（如果是简单问题）

请只输出 JSON 格式，不要其他内容。"""
            else:
                # 已有子任务，检查进度并汇总
                completed = sum(1 for st in subtasks if st.get("completed", False))
                total = len(subtasks)
                
                prompt = f"""任务执行进度：{completed}/{total}

各 Agent 执行结果：
{json.dumps(agent_results, ensure_ascii=False, indent=2)}

请：
1. 检查是否所有子任务都已完成
2. 如果完成，汇总所有结果生成最终回复
3. 如果未完成，继续分配剩余任务

请只输出 JSON 格式。"""
            
            # 调用主管 Agent
            messages = [
                HumanMessage(content=prompt),
            ]
            
            # 使用主管 Agent 的 LLM
            response = supervisor.llm.invoke(messages)
            
            # 解析响应
            try:
                # 尝试提取 JSON
                import re
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    decision = json.loads(json_match.group())
                else:
                    decision = {"action": "reply", "content": response.content}
            except:
                decision = {"action": "reply", "content": response.content}
            
            # 更新状态
            updates = {}
            
            if decision.get("action") == "decompose" and "subtasks" in decision:
                # 分解任务
                updates["subtasks"] = decision["subtasks"]
                updates["current_subtask"] = 0
                logger.info(f"任务已分解为 {len(decision['subtasks'])} 个子任务")
            
            elif decision.get("action") == "summarize":
                # 汇总结果
                updates["final_result"] = decision.get("content", "")
                updates["task_complete"] = True
                logger.info("任务已完成，结果已汇总")
            
            elif decision.get("action") == "reply":
                # 直接回复
                updates["final_result"] = decision.get("content", "")
                updates["task_complete"] = True
                logger.info("直接回复用户")
            
            return updates
        
        except Exception as e:
            logger.exception(f"主管节点执行失败：{e}")
            return {
                "final_result": f"错误：{str(e)}",
                "task_complete": True,
            }
    
    def _expert_node(self, state: MultiAgentState, role: AgentRole) -> Dict[str, Any]:
        """
        专家节点：执行子任务（同步版本）
        
        参数:
            state: 当前状态
            role: Agent 角色
        
        返回:
            执行结果
        """
        try:
            current_idx = state.get("current_subtask", 0)
            subtasks = state.get("subtasks", [])
            
            if current_idx >= len(subtasks):
                return {}
            
            # 获取当前子任务
            subtask = subtasks[current_idx]
            subtask_role = subtask.get("role", "executor")
            subtask_description = subtask.get("task", "")
            
            logger.info(f"专家 Agent 执行任务：{subtask_role} - {subtask_description[:50]}...")
            
            # 获取对应的 Agent
            try:
                agent_role = AgentRole(subtask_role)
            except Exception:
                agent_role = AgentRole.EXECUTOR
            
            if agent_role not in self.agents:
                agent_role = AgentRole.EXECUTOR
            
            expert = self.agents[agent_role]
            
            # 执行子任务（使用嵌套事件循环）
            import asyncio
            
            try:
                # 尝试在当前事件循环中运行
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果事件循环正在运行，使用同步方式调用
                    result = expert.run_sync(
                        input_text=subtask_description,
                        session_key=f"subtask_{current_idx}",
                    )
                else:
                    # 否则使用 asyncio.run
                    result = asyncio.run(
                        expert.run(
                            input_text=subtask_description,
                            session_key=f"subtask_{current_idx}",
                        )
                    )
            except RuntimeError:
                # 没有事件循环，创建新的
                result = asyncio.run(
                    expert.run(
                        input_text=subtask_description,
                        session_key=f"subtask_{current_idx}",
                    )
                )
            
            # 更新状态
            agent_results = state.get("agent_results", {}).copy()
            agent_results[f"{agent_role.value}_{current_idx}"] = {
                "role": agent_role.value,
                "task": subtask_description,
                "result": result.get("output", ""),
                "success": result.get("success", False),
            }
            
            return {
                "agent_results": agent_results,
                "current_subtask": current_idx + 1,
            }
        
        except Exception as e:
            logger.exception(f"专家节点执行失败：{e}")
            return {
                "agent_results": {
                    f"error_{state.get('current_subtask', 0)}": {
                        "error": str(e),
                        "success": False,
                    }
                },
                "current_subtask": state.get("current_subtask", 0) + 1,
            }
    
    def _route_task(self, state: MultiAgentState) -> str:
        """
        路由任务到合适的节点
        
        参数:
            state: 当前状态
        
        返回:
            下一个节点名称或 "end"
        """
        # 检查任务是否完成
        if state.get("task_complete", False):
            return "end"
        
        # 检查是否有子任务
        subtasks = state.get("subtasks", [])
        current_idx = state.get("current_subtask", 0)
        
        if not subtasks:
            # 首次分析，返回主管继续分解
            return "supervisor"
        
        if current_idx >= len(subtasks):
            # 所有子任务已完成，返回主管汇总
            return "supervisor"
        
        # 获取当前子任务的角色
        subtask = subtasks[current_idx]
        subtask_role = subtask.get("role", "executor")
        
        return f"expert_{subtask_role}"
    
    async def run(
        self,
        task: str,
        session_key: str = "default",
    ) -> Dict[str, Any]:
        """
        运行多 Agent 协作
        
        参数:
            task: 任务描述
            session_key: 会话键
        
        返回:
            执行结果
        """
        logger.info(f"启动多 Agent 协作：{task[:50]}...")
        
        try:
            # 准备初始状态
            initial_state = MultiAgentState(
                messages=[HumanMessage(content=task)],
                task=task,
                subtasks=[],
                current_subtask=0,
                agent_results={},
                final_result="",
                task_complete=False,
            )
            
            # 执行协作图
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: list(self.graph.stream(
                    initial_state,
                    config={"configurable": {"thread_id": session_key}},
                ))
            )
            
            # 提取最终结果
            final_state = {}
            for step in result:
                for node_name, node_output in step.items():
                    final_state.update(node_output)
            
            output = final_state.get("final_result", "未生成结果")
            
            logger.info(f"多 Agent 协作完成：{len(output)} 字符")
            
            return {
                "success": True,
                "output": output,
                "session_key": session_key,
                "subtasks": final_state.get("subtasks", []),
                "agent_results": final_state.get("agent_results", {}),
            }
        
        except Exception as e:
            logger.exception(f"多 Agent 协作失败：{e}")
            return {
                "success": False,
                "error": str(e),
            }


# ============================================================================
# 便捷函数
# ============================================================================

def create_multi_agent_system(
    roles: Optional[List[AgentRole]] = None,
    tool_registry: Optional[Any] = None,
    workspace_path: Optional[str] = None,
) -> MultiAgentCollaboration:
    """
    创建多 Agent 协作系统的便捷函数
    
    参数:
        roles: 要启用的 Agent 角色列表
        tool_registry: 工具注册表
        workspace_path: 工作区路径
    
    返回:
        MultiAgentCollaboration 实例
    """
    if roles:
        agent_definitions = {
            role: DEFAULT_AGENTS[role]
            for role in roles
            if role in DEFAULT_AGENTS
        }
    else:
        agent_definitions = DEFAULT_AGENTS
    
    return MultiAgentCollaboration(
        agent_definitions=agent_definitions,
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
    
    # 创建多 Agent 系统
    multi_agent = create_multi_agent_system(
        workspace_path=str(Path.home() / ".pyclaw" / "workspace"),
    )
    
    # 测试运行
    async def test():
        result = await multi_agent.run(
            task="帮我查询今天的天气，并写一封邮件给我的同事告知天气情况。",
            session_key="test_multi_agent",
        )
        print(f"\n结果：{result['output']}\n")
        print(f"子任务数：{len(result.get('subtasks', []))}")
        print(f"Agent 执行结果：{len(result.get('agent_results', {}))}")
    
    asyncio.run(test())
