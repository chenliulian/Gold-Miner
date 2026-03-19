#!/usr/bin/env python3
"""
测试 execute_sql_with_priority 方法
对比不同 priority 的执行时间
"""
import os
import sys
import time
from pathlib import Path

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


def test_odps_connection():
    """测试 ODPS 连接"""
    print("=" * 70)
    print("ODPS 连接初始化")
    print("=" * 70)
    
    config = OdpsConfig(
        access_id=os.getenv("ODPS_ACCESS_ID"),
        access_key=os.getenv("ODPS_ACCESS_KEY"),
        project=os.getenv("ODPS_PROJECT"),
        endpoint=os.getenv("ODPS_ENDPOINT"),
        quota=os.getenv("ODPS_QUOTA", ""),
    )
    
    print(f"Project: {config.project}")
    print(f"Endpoint: {config.endpoint}")
    print(f"Quota: {config.quota or '未设置'}")
    
    client = OdpsClient(config)
    print("✅ ODPS 客户端初始化成功")
    return client


def test_with_priority(client: OdpsClient, priority: int):
    """测试指定优先级的执行"""
    print(f"\n{'='*70}")
    print(f"测试 priority={priority} ({'较高' if priority <= 5 else '较低'}优先级)")
    print(f"{'='*70}")
    
    start_time = time.time()
    
    try:
        df, instance_id = client.execute_sql_with_priority(
            sql=TEST_SQL,
            priority=priority,
            limit=100,
            enable_log=True
        )
        
        elapsed_time = time.time() - start_time
        
        print(f"\n{'='*70}")
        print(f"✅ Priority={priority} 执行成功!")
        print(f"Instance ID: {instance_id}")
        print(f"总耗时: {elapsed_time:.2f} 秒")
        print(f"返回行数: {len(df)}")
        
        if not df.empty:
            print(f"\n查询结果:")
            print(df.to_string(index=False))
        
        return {
            "priority": priority,
            "success": True,
            "instance_id": instance_id,
            "elapsed_time": elapsed_time,
            "rows": len(df)
        }
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"\n❌ Priority={priority} 执行失败: {e}")
        return {
            "priority": priority,
            "success": False,
            "error": str(e),
            "elapsed_time": elapsed_time
        }


def print_comparison(results: list):
    """打印对比结果"""
    print("\n" + "=" * 70)
    print("Priority 执行时间对比")
    print("=" * 70)
    
    print(f"\n{'Priority':<12} {'状态':<10} {'耗时(秒)':<12} {'返回行数':<10}")
    print("-" * 70)
    
    for result in results:
        priority = f"priority={result['priority']}"
        status = "✅ 成功" if result["success"] else "❌ 失败"
        elapsed = f"{result['elapsed_time']:.2f}"
        rows = str(result.get("rows", "N/A"))
        print(f"{priority:<12} {status:<10} {elapsed:<12} {rows:<10}")
    
    # 计算时间差
    if len(results) >= 2 and all(r["success"] for r in results):
        print("\n" + "-" * 70)
        time_diff = results[1]["elapsed_time"] - results[0]["elapsed_time"]
        faster = results[0]["priority"] if results[0]["elapsed_time"] < results[1]["elapsed_time"] else results[1]["priority"]
        print(f"时间差: {abs(time_diff):.2f} 秒")
        print(f"priority={faster} 执行更快")


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("execute_sql_with_priority 方法测试 - Priority 对比")
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
        client = test_odps_connection()
        
        print(f"\n测试 SQL:\n{TEST_SQL}")
        
        results = []
        
        # 测试 priority=3
        result1 = test_with_priority(client, priority=3)
        results.append(result1)
        
        # 等待 5 秒避免资源竞争
        print("\n等待 5 秒...")
        time.sleep(5)
        
        # 测试 priority=7
        result2 = test_with_priority(client, priority=7)
        results.append(result2)
        
        # 打印对比结果
        print_comparison(results)
        
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
