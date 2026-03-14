#!/usr/bin/env python3
"""
测试 pyclaw-web 聊天接口
"""

import requests
import json
import time

# 配置
BASE_URL = "http://127.0.0.1:18800"
SESSION_ID = f"test_{int(time.time())}"
MESSAGE = "你好，测试多 Agent 功能"

def test_chat():
    print("=" * 60)
    print("测试 pyclaw-web 聊天接口")
    print("=" * 60)
    
    # 1. 创建会话
    print(f"\n1. 创建会话：{SESSION_ID}")
    response = requests.post(
        f"{BASE_URL}/api/sessions",
        json={"session_id": SESSION_ID, "mode": "multi"}
    )
    print(f"   状态码：{response.status_code}")
    print(f"   响应：{response.json()}")
    
    # 2. 发送消息
    print(f"\n2. 发送消息：{MESSAGE}")
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "session_id": SESSION_ID,
                "message": MESSAGE,
                "mode": "multi"
            },
            timeout=300  # 5 分钟超时
        )
        
        elapsed = time.time() - start_time
        print(f"   耗时：{elapsed:.2f} 秒")
        print(f"   状态码：{response.status_code}")
        
        result = response.json()
        print(f"   响应：")
        print(f"     success: {result.get('success')}")
        print(f"     message: {result.get('message', '')[:200]}")
        
        if result.get('metadata'):
            print(f"     metadata: {json.dumps(result.get('metadata'), indent=2, ensure_ascii=False)[:500]}")
        
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"   ❌ 请求超时（耗时：{elapsed:.2f} 秒）")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"   ❌ 错误：{e}（耗时：{elapsed:.2f} 秒）")
    
    # 3. 查看会话
    print(f"\n3. 查看会话状态")
    response = requests.get(f"{BASE_URL}/api/sessions/{SESSION_ID}")
    print(f"   状态码：{response.status_code}")
    print(f"   响应：{response.json()}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_chat()
