#!/usr/bin/env python3
"""
Agent 系统测试
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestLangGraphAgentConfig:
    """测试 Agent 配置"""
    
    def test_default_config(self):
        """测试默认配置"""
        from agents.langgraph_agent import LangGraphAgentConfig
        
        config = LangGraphAgentConfig()
        
        assert config.name == "assistant"
        assert config.model == "qwen3.5-plus"
        assert config.provider == "bailian"
        assert config.max_iterations == 10
    
    def test_custom_config(self):
        """测试自定义配置"""
        from agents.langgraph_agent import LangGraphAgentConfig
        
        config = LangGraphAgentConfig(
            name="custom_agent",
            model="gpt-4",
            temperature=0.5,
            max_iterations=20,
        )
        
        assert config.name == "custom_agent"
        assert config.model == "gpt-4"
        assert config.temperature == 0.5
        assert config.max_iterations == 20


class TestMultiAgentRoles:
    """测试多 Agent 角色"""
    
    def test_agent_role_enum(self):
        """测试 Agent 角色枚举"""
        from agents.multi_agent import AgentRole
        
        assert AgentRole.SUPERVISOR.value == "supervisor"
        assert AgentRole.RESEARCHER.value == "researcher"
        assert AgentRole.CODER.value == "coder"
        assert AgentRole.WRITER.value == "writer"
        assert AgentRole.ANALYST.value == "analyst"
        assert AgentRole.EXECUTOR.value == "executor"
    
    def test_default_agents(self):
        """测试默认 Agent 定义"""
        from agents.multi_agent import DEFAULT_AGENTS, AgentRole
        
        assert AgentRole.SUPERVISOR in DEFAULT_AGENTS
        assert AgentRole.RESEARCHER in DEFAULT_AGENTS
        assert len(DEFAULT_AGENTS) >= 4


class TestAgentState:
    """测试 Agent 状态"""
    
    def test_agent_state_structure(self):
        """测试 Agent 状态结构"""
        from agents.langgraph_agent import AgentState
        
        # AgentState 是 TypedDict，测试其键
        assert "messages" in AgentState.__annotations__
        assert "system_prompt" in AgentState.__annotations__
        assert "max_iterations" in AgentState.__annotations__
        assert "current_iteration" in AgentState.__annotations__
        assert "task_complete" in AgentState.__annotations__


class TestMultiAgentState:
    """测试多 Agent 状态"""
    
    def test_multi_agent_state_structure(self):
        """测试多 Agent 状态结构"""
        from agents.multi_agent import MultiAgentState
        
        assert "messages" in MultiAgentState.__annotations__
        assert "task" in MultiAgentState.__annotations__
        assert "subtasks" in MultiAgentState.__annotations__
        assert "agent_results" in MultiAgentState.__annotations__
        assert "final_result" in MultiAgentState.__annotations__
        assert "task_complete" in MultiAgentState.__annotations__


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
