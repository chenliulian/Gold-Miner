"""
测试 self_improvement skill 的去重逻辑

验证修复：防止 Agent 反复调用 self_improvement 记录相同的用户反馈
"""

import sys
import time
sys.path.insert(0, '/Users/shmichenliulian/GoldMiner/src')

from gold_miner.agent import AgentState, _recent_self_improvements, _SELF_IMPROVEMENT_COOLDOWN, _MAX_RECENT_SELF_IMPROVEMENTS


def test_self_improvement_dedup():
    """测试 self_improvement 调用去重逻辑"""
    
    print("=" * 60)
    print("测试 self_improvement 去重逻辑")
    print("=" * 60)
    
    # 创建两个 AgentState 实例（模拟两次 run() 调用）
    state1 = AgentState()
    state2 = AgentState()
    
    # 测试用例 1: 完全相同的反馈
    print("\n[测试1] 完全相同的反馈应该被去重")
    args1 = {
        "summary": "黄金眼表统计消耗和下载数不需要过滤event_type",
        "details": "用户反馈：黄金眼表统计消耗和下载数不需要过滤event_type",
        "category": "correction"
    }
    
    # 第一次调用 - 应该允许
    is_dup1 = state1.is_self_improvement_recently_called(args1)
    print(f"  第一次调用 (state1): is_duplicate={is_dup1}, expected=False")
    assert is_dup1 == False, "第一次调用不应该被认为是重复的"
    state1.record_self_improvement_call(args1)
    print(f"  ✓ 已记录到全局变量，当前记录数: {len(_recent_self_improvements)}")
    
    # 第二次调用（不同的 state 实例，相同内容）- 应该被去重
    is_dup2 = state2.is_self_improvement_recently_called(args1)
    print(f"  第二次调用 (state2, 相同内容): is_duplicate={is_dup2}, expected=True")
    assert is_dup2 == True, "相同内容在冷却时间内应该被认为是重复的"
    print(f"  ✓ 正确识别为重复调用，已跳过")
    
    # 测试用例 2: 相似内容（包含核心关键词）
    print("\n[测试2] 包含核心关键词的内容应该被去重")
    args2 = {
        "summary": "用户纠正：黄金眼表统计消耗和下载数不需要过滤event_type",
        "details": "用户纠正：黄金眼表统计消耗和下载数不需要过滤event_type",
        "category": "correction"
    }
    is_dup3 = state2.is_self_improvement_recently_called(args2)
    print(f"  相似内容调用: is_duplicate={is_dup3}, expected=True")
    assert is_dup3 == True, "相似内容应该被认为是重复的"
    print(f"  ✓ 正确识别为重复调用（内容相似）")
    
    # 测试用例 3: 完全不同的反馈
    print("\n[测试3] 完全不同的反馈应该允许记录")
    args3 = {
        "summary": "修复SQL查询中的分区字段错误",
        "details": "用户反馈：查询应该用dt而不是dh作为分区字段",
        "category": "correction"
    }
    is_dup4 = state2.is_self_improvement_recently_called(args3)
    print(f"  不同内容调用: is_duplicate={is_dup4}, expected=False")
    assert is_dup4 == False, "不同内容不应该被认为是重复的"
    state2.record_self_improvement_call(args3)
    print(f"  ✓ 已记录到全局变量，当前记录数: {len(_recent_self_improvements)}")
    
    # 测试用例 4: 验证冷却时间
    print("\n[测试4] 验证冷却时间机制")
    print(f"  当前冷却时间: {_SELF_IMPROVEMENT_COOLDOWN}秒")
    print(f"  当前记录数: {len(_recent_self_improvements)}")
    
    # 验证记录被保存
    assert len(_recent_self_improvements) == 2, "应该有两条记录"
    print(f"  ✓ 两条记录都已保存到全局变量")
    
    print("\n" + "=" * 60)
    print("所有测试通过！✓")
    print("=" * 60)
    print("\n修复验证总结:")
    print("1. ✓ 相同反馈在冷却时间内被正确去重")
    print("2. ✓ 相似反馈被正确识别并去重")
    print("3. ✓ 不同反馈允许正常记录")
    print("4. ✓ 跨 AgentState 实例共享记录（类变量）")


def test_content_similarity():
    """测试内容相似度算法"""
    print("\n" + "=" * 60)
    print("测试内容相似度算法")
    print("=" * 60)
    
    state = AgentState()
    
    test_cases = [
        ("黄金眼表统计消耗", "黄金眼表消耗统计", False),  # 字符差异较大，不算相似
        ("不需要过滤event_type", "不需要event_type过滤", False),  # 字符差异较大，不算相似
        ("用户反馈: XXX", "用户纠正: XXX", False),  # 不同前缀，不算相似
        ("完全不相同的内容", "另一个完全不同的内容", False),
        ("event_type过滤", "event_type过滤", True),  # 完全相同
        ("黄金眼表统计消耗和下载数不需要过滤event_type", "用户纠正：黄金眼表统计消耗和下载数不需要过滤event_type", True),  # 包含关系
    ]
    
    for content1, content2, expected in test_cases:
        result = state._is_similar_content(content1, content2)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{content1[:20]}...' vs '{content2[:20]}...' -> {result}, expected={expected}")
        assert result == expected, f"相似度检查失败: {content1} vs {content2}"
    
    print("\n  所有相似度测试通过！✓")


def test_cooldown_mechanism():
    """测试冷却时间机制（模拟）"""
    print("\n" + "=" * 60)
    print("测试冷却时间机制")
    print("=" * 60)
    
    # 清空之前的记录
    _recent_self_improvements.clear()
    
    state = AgentState()
    args = {
        "summary": "测试冷却时间",
        "details": "这是一个测试",
        "category": "test"
    }
    
    # 记录一次
    state.record_self_improvement_call(args)
    print(f"  已记录，当前时间戳: {_recent_self_improvements[-1]['timestamp']:.2f}")
    
    # 立即检查 - 应该重复
    is_dup = state.is_self_improvement_recently_called(args)
    print(f"  立即检查: is_duplicate={is_dup}, expected=True")
    assert is_dup == True
    
    # 修改记录时间戳为过去（模拟时间流逝）
    old_time = time.time() - _SELF_IMPROVEMENT_COOLDOWN - 1
    _recent_self_improvements[-1]['timestamp'] = old_time
    print(f"  修改时间戳为: {old_time:.2f} (超过冷却时间)")
    
    # 再次检查 - 应该不重复
    is_dup2 = state.is_self_improvement_recently_called(args)
    print(f"  冷却后检查: is_duplicate={is_dup2}, expected=False")
    assert is_dup2 == False
    
    print("\n  冷却时间机制测试通过！✓")


if __name__ == "__main__":
    try:
        test_self_improvement_dedup()
        test_content_similarity()
        test_cooldown_mechanism()
        print("\n" + "=" * 60)
        print("🎉 所有测试通过！修复验证成功。")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
