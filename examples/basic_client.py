#!/usr/bin/env python3
"""
PyClaw 基础客户端示例
=====================

演示如何连接到 PyClaw Gateway 并发送请求。

使用方式：
    python examples/basic_client.py
"""

import asyncio
import json
import websockets


async def connect_to_gateway():
    """
    连接到 PyClaw Gateway
    
    演示完整的连接、认证、请求流程。
    """
    # Gateway 地址
    uri = "ws://127.0.0.1:18789"
    
    print(f"🔌 连接到 {uri}...")
    
    try:
        async with websockets.connect(uri) as ws:
            print("✓ WebSocket 连接成功")
            
            # 1. 发送连接请求
            connect_request = {
                "type": "req",
                "id": "connect-1",
                "method": "connect",
                "params": {
                    # "auth": {"token": "your-token"}  # 如果启用了认证
                },
            }
            
            print("\n📤 发送连接请求...")
            await ws.send(json.dumps(connect_request))
            
            # 接收响应
            response = await ws.recv()
            data = json.loads(response)
            
            if data.get("ok"):
                print("✓ 连接成功")
                print(f"   服务器状态：{data['payload'].get('status')}")
                print(f"   运行时间：{data['payload'].get('uptime')}秒")
            else:
                print(f"✗ 连接失败：{data.get('error')}")
                return
            
            # 2. 发送健康检查
            print("\n📤 发送健康检查...")
            health_request = {
                "type": "req",
                "id": "health-1",
                "method": "health",
                "params": {},
            }
            
            await ws.send(json.dumps(health_request))
            response = await ws.recv()
            data = json.loads(response)
            
            if data.get("ok"):
                print("✓ 健康检查通过")
                print(f"   状态：{data['payload'].get('status')}")
                print(f"   客户端数：{data['payload'].get('clients')}")
            
            # 3. 发送代理执行请求
            print("\n📤 发送代理执行请求...")
            agent_request = {
                "type": "req",
                "id": "agent-1",
                "method": "agent",
                "params": {
                    "sessionKey": "agent:main:main",
                    "messages": [
                        {"role": "user", "content": "你好，请介绍一下自己"}
                    ],
                },
            }
            
            await ws.send(json.dumps(agent_request))
            response = await ws.recv()
            data = json.loads(response)
            
            if data.get("ok"):
                print("✓ 代理执行已接受")
                print(f"   运行 ID: {data['payload'].get('runId')}")
                print(f"   状态：{data['payload'].get('status')}")
            
            print("\n✅ 测试完成")
    
    except ConnectionRefusedError:
        print("✗ 连接被拒绝")
        print("   请确保 Gateway 正在运行：python main.py")
    except Exception as e:
        print(f"✗ 错误：{e}")


async def listen_for_events():
    """
    监听服务器事件
    
    演示如何接收服务器推送的事件。
    """
    uri = "ws://127.0.0.1:18789"
    
    print(f"👂 监听事件：{uri}")
    
    try:
        async with websockets.connect(uri) as ws:
            # 先连接
            await ws.send(json.dumps({
                "type": "req",
                "id": "connect-1",
                "method": "connect",
                "params": {},
            }))
            
            await ws.recv()  # 忽略连接响应
            
            print("✓ 开始监听事件...")
            print("   (按 Ctrl+C 停止)")
            print()
            
            # 持续监听事件
            while True:
                try:
                    message = await asyncio.wait_for(ws.recv(), timeout=30)
                    data = json.loads(message)
                    
                    if data.get("type") == "event":
                        event_type = data.get("event")
                        payload = data.get("payload", {})
                        
                        print(f"📨 事件：{event_type}")
                        print(f"   数据：{json.dumps(payload, indent=2)}")
                        print()
                
                except asyncio.TimeoutError:
                    # 发送心跳
                    await ws.send(json.dumps({
                        "type": "req",
                        "id": "ping-1",
                        "method": "health",
                        "params": {},
                    }))
    
    except KeyboardInterrupt:
        print("\n👋 停止监听")
    except Exception as e:
        print(f"✗ 错误：{e}")


async def main():
    """主函数"""
    print("=" * 60)
    print("PyClaw 客户端示例")
    print("=" * 60)
    print()
    
    # 运行基础连接测试
    await connect_to_gateway()
    
    print()
    print("-" * 60)
    print()
    
    # 询问是否监听事件
    print("是否开始监听事件？(y/N)")
    choice = input("> ").strip().lower()
    
    if choice == "y":
        await listen_for_events()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 再见")
