#!/usr/bin/env python3
"""
LangChain 多 Agent 编排示例
===========================

演示如何使用 LangChain 实现多 Agent 协作。

场景：
1. 用户提问
2. Router 路由到合适的 Agent
3. 多个 Agent 协作完成任务
4. 聚合结果返回给用户
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.langchain_agent import (
    LangChainAgent,
    MultiAgentOrchestrator,
    AgentConfig,
    create_coding_agent,
    create_writing_agent,
    create_chat_agent,
)
from tools.registry import ToolRegistry


async def demo_single_agent():
    """演示单 Agent 使用"""
    print("=" * 60)
    print("单 Agent 演示")
    print("=" * 60)
    print()
    
    # 创建 Agent
    agent = create_chat_agent()
    
    # 测试对话
    test_questions = [
        "你好，请介绍一下自己",
        "Python 中如何实现装饰器？",
        "帮我写一个快速排序",
    ]
    
    for question in test_questions:
        print(f"👤 用户：{question}")
        result = await agent.run(question)
        
        if result["success"]:
            print(f"🤖 助手：{result['output'][:200]}...")
        else:
            print(f"❌ 错误：{result.get('error')}")
        print()


async def demo_multi_agent():
    """演示多 Agent 协作"""
    print("=" * 60)
    print("多 Agent 协作演示")
    print("=" * 60)
    print()
    
    # 创建编排器
    orchestrator = MultiAgentOrchestrator()
    
    # 添加多个 Agent
    orchestrator.add_agent("coding", create_coding_agent())
    orchestrator.add_agent("writing", create_writing_agent())
    orchestrator.add_agent("chat", create_chat_agent())
    
    print(f"✅ 已加载 {len(orchestrator.agents)} 个 Agent")
    print()
    
    # 测试任务
    test_tasks = [
        "帮我写一个 Python 函数，计算斐波那契数列",
        "写一篇关于人工智能的短文",
        "你好，今天天气不错",
        "帮我分析一下这段代码的性能问题",
    ]
    
    for task in test_tasks:
        print(f"📋 任务：{task}")
        
        result = await orchestrator.execute_task(task)
        
        if result["success"]:
            print(f"✅ 使用 Agent: {result.get('agent_used', 'unknown')}")
            print(f"📝 结果：{result['output'][:200]}...")
        else:
            print(f"❌ 失败：{result.get('error')}")
        print()
    
    # 显示统计
    print("📊 编排器统计:")
    stats = orchestrator.get_stats()
    print(f"   Agent 数量：{stats['agent_count']}")
    for name, agent_stats in stats['agents'].items():
        print(f"   - {name}: {agent_stats['model']}")


async def demo_custom_agent():
    """演示自定义 Agent"""
    print("=" * 60)
    print("自定义 Agent 演示")
    print("=" * 60)
    print()
    
    # 创建自定义 Agent
    config = AgentConfig(
        name="custom-assistant",
        role="custom",
        model="gpt-4",
        system_prompt="""你是一个全能的 AI 助手。
你擅长解决各种问题，提供有用的建议。
请用简洁清晰的语言回答。""",
        memory_type="buffer",
    )
    
    # 创建工具注册表
    tool_registry = ToolRegistry()
    
    # 创建 Agent
    agent = LangChainAgent(
        config=config,
        tool_registry=tool_registry,
    )
    
    # 测试
    questions = [
        "今天北京天气如何？",
        "推荐几本好看的书",
    ]
    
    for question in questions:
        print(f"👤 用户：{question}")
        result = await agent.run(question)
        
        if result["success"]:
            print(f"🤖 助手：{result['output'][:200]}...")
        print()


async def main():
    """主函数"""
    print()
    print("🦮 PyClaw LangChain Agent 演示")
    print()
    
    # 选择演示模式
    print("选择演示模式:")
    print("1) 单 Agent")
    print("2) 多 Agent 协作")
    print("3) 自定义 Agent")
    print("4) 全部演示")
    print()
    
    choice = input("请输入选项 [1-4]: ").strip()
    
    if choice == "1":
        await demo_single_agent()
    elif choice == "2":
        await demo_multi_agent()
    elif choice == "3":
        await demo_custom_agent()
    elif choice == "4":
        await demo_single_agent()
        await demo_multi_agent()
        await demo_custom_agent()
    else:
        print("无效选项")
        return
    
    print()
    print("✅ 演示完成！")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 再见")
    except Exception as e:
        print(f"❌ 错误：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
