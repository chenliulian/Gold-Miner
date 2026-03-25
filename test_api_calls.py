#!/usr/bin/env python3
"""测试 API 调用"""

import requests
import json

BASE_URL = "http://127.0.0.1:5001"

def test_get_sessions():
    """测试获取会话列表"""
    try:
        resp = requests.get(f"{BASE_URL}/sessions", timeout=5)
        data = resp.json()
        print(f"✓ GET /sessions: success={data.get('success')}, sessions={len(data.get('sessions', []))}")
        return data
    except Exception as e:
        print(f"✗ GET /sessions: {e}")
        return None

def test_create_session():
    """测试创建新会话"""
    try:
        resp = requests.post(
            f"{BASE_URL}/sessions/new",
            json={"title": "测试对话"},
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        data = resp.json()
        print(f"✓ POST /sessions/new: success={data.get('success')}, session_id={data.get('session_id', 'N/A')}")
        return data
    except Exception as e:
        print(f"✗ POST /sessions/new: {e}")
        return None

def test_get_session(session_id):
    """测试获取单个会话"""
    try:
        resp = requests.get(f"{BASE_URL}/sessions/{session_id}", timeout=5)
        data = resp.json()
        print(f"✓ GET /sessions/{session_id[:20]}...: success={data.get('success')}")
        return data
    except Exception as e:
        print(f"✗ GET /sessions/{session_id}: {e}")
        return None

if __name__ == "__main__":
    print("API 测试:\n")
    
    # 测试获取会话列表
    sessions_data = test_get_sessions()
    
    # 测试创建新会话
    new_session = test_create_session()
    
    # 如果创建成功，测试获取该会话
    if new_session and new_session.get('success'):
        test_get_session(new_session['session_id'])
    
    print("\n所有 API 测试完成")
