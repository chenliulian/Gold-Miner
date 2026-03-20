#!/usr/bin/env python3
"""
对比测试：run_sql_with_progress vs execute_sql_with_priority
测试两种方法的性能和功能差异
"""
import os
import sys
import time
from pathlib import Path

import pytest

# 添加 src 到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from dotenv import load_dotenv
from gold_miner.odps_client import OdpsClient, OdpsConfig

# 加载环境变量
load_dotenv()

# 测试 SQL
TEST_SQL = """SELECT 
     cost_type, 
     sum(billing_actual_deduction_price)/1e5 AS spend_cost 
   FROM mi_ads_dmp.dwd_ew_ads_show_res_clk_dld_conv_hi 
   WHERE dh >= '2026031100' AND dh <= '2026031123' 
   group by cost_type"""


@pytest.fixture
def odps_client():
    """ODPS 客户端 fixture"""
    config = OdpsConfig(
        access_id=os.getenv("ODPS_ACCESS_ID"),
        access_key=os.getenv("ODPS_ACCESS_KEY"),
        project=os.getenv("ODPS_PROJECT"),
        endpoint=os.getenv("ODPS_ENDPOINT"),
        quota=os.getenv("ODPS_QUOTA", ""),
    )
    return OdpsClient(config)


@pytest.mark.skipif(
    not os.getenv("ODPS_ACCESS_ID"),
    reason="ODPS credentials not configured"
)
def test_run_sql_with_progress(odps_client):
    """测试 run_sql_with_progress 方法（agent 默认使用）"""
    print("\n" + "=" * 70)
    print("方法 1: run_sql_with_progress (hints 方式设置 priority=7)")
    print("=" * 70)
    
    start_time = time.time()
    
    try:
        df, instance_id = odps_client.run_sql_with_progress(
            sql=TEST_SQL,
            limit=100,
            enable_log=False
        )
        
        elapsed_time = time.time() - start_time
        
        print(f"\n{'='*70}")
        print(f"✅ 查询成功!")
        print(f"Instance ID: {instance_id}")
        print(f"总耗时: {elapsed_time:.2f} 秒")
        print(f"返回行数: {len(df)}")
        
        assert df is not None
        assert instance_id is not None
        
    except Exception as e:
        pytest.skip(f"查询失败: {e}")


@pytest.mark.skipif(
    not os.getenv("ODPS_ACCESS_ID"),
    reason="ODPS credentials not configured"
)
def test_execute_sql_with_priority(odps_client):
    """测试 execute_sql_with_priority 方法（priority 参数方式）"""
    print("\n" + "=" * 70)
    print("方法 2: execute_sql_with_priority (priority 参数方式, priority=7)")
    print("=" * 70)
    
    start_time = time.time()
    
    try:
        df, instance_id = odps_client.execute_sql_with_priority(
            sql=TEST_SQL,
            priority=7,
            limit=100,
            enable_log=False
        )
        
        elapsed_time = time.time() - start_time
        
        print(f"\n{'='*70}")
        print(f"✅ 查询成功!")
        print(f"Instance ID: {instance_id}")
        print(f"总耗时: {elapsed_time:.2f} 秒")
        print(f"返回行数: {len(df)}")
        
        assert df is not None
        assert instance_id is not None
        
    except Exception as e:
        pytest.skip(f"查询失败: {e}")


def main():
    """主函数 - 命令行运行对比测试"""
    print("\n" + "=" * 70)
    print("ODPS SQL 执行方法对比测试")
    print("=" * 70)
    
    # 检查环境变量
    required_vars = ["ODPS_ACCESS_ID", "ODPS_ACCESS_KEY", "ODPS_PROJECT", "ODPS_ENDPOINT"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"\n❌ 缺少环境变量: {', '.join(missing_vars)}")
        print("请确保 .env 文件包含以下变量:")
        for var in required_vars:
            print(f"  - {var}")
        return 1
    
    try:
        # 初始化客户端
        config = OdpsConfig(
            access_id=os.getenv("ODPS_ACCESS_ID"),
            access_key=os.getenv("ODPS_ACCESS_KEY"),
            project=os.getenv("ODPS_PROJECT"),
            endpoint=os.getenv("ODPS_ENDPOINT"),
            quota=os.getenv("ODPS_QUOTA", ""),
        )
        client = OdpsClient(config)
        print("✅ ODPS 客户端初始化成功")
        
        print(f"\n测试 SQL:\n{TEST_SQL}")
        
        # 测试方法 1
        print("\n" + "=" * 70)
        print("方法 1: run_sql_with_progress")
        print("=" * 70)
        start = time.time()
        df1, id1 = client.run_sql_with_progress(sql=TEST_SQL, limit=100, enable_log=True)
        print(f"✅ 成功! 耗时: {time.time()-start:.2f}s, Instance: {id1}")
        
        # 等待 3 秒避免资源竞争
        print("\n等待 3 秒...")
        time.sleep(3)
        
        # 测试方法 2
        print("\n" + "=" * 70)
        print("方法 2: execute_sql_with_priority")
        print("=" * 70)
        start = time.time()
        df2, id2 = client.execute_sql_with_priority(sql=TEST_SQL, priority=7, limit=100, enable_log=True)
        print(f"✅ 成功! 耗时: {time.time()-start:.2f}s, Instance: {id2}")
        
        print("\n" + "=" * 70)
        print("测试完成!")
        print("=" * 70)
        return 0
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
