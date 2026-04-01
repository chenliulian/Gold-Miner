#!/usr/bin/env python3
"""创建测试用户 test123/123456"""

import sys
import os

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gold_miner.auth.user_store import UserStore
from gold_miner.auth.service import hash_password

def create_test_user():
    """创建测试用户"""
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    user_store = UserStore(data_dir)

    # 检查用户是否已存在
    existing_user = user_store.get_user_by_username('test123')
    if existing_user:
        print("用户 test123 已存在")
        return

    # 创建用户数据
    from datetime import datetime
    now = datetime.now().isoformat()
    user_data = {
        "username": "test123",
        "password_hash": hash_password("123456"),
        "name": "测试用户",
        "role": "analyst",
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }

    user = user_store.create_user(user_data)
    print(f"用户创建成功: {user.id}")
    print(f"用户名: test123")
    print(f"密码: 123456")

if __name__ == "__main__":
    create_test_user()
