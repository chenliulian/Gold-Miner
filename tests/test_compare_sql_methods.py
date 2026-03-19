#!/usr/bin/env python3
"""
对比测试：run_sql_with_progress vs execute_sql_with_priority
测试两种方法的性能和功能差异
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


def test_run_sql_with_progress(client: OdpsClient):
    """测试 run_sql_with_progress 方法（agent 默认使用）"""
    print("\n" + "=" * 70)
    print("方法 1: run_sql_with_progress (hints 方式设置 priority=7)")
    print("=" * 70)
    
    start_time = time.time()
    
    try:
        df, instance_id = client.run_sql_with_progress(
            sql=TEST_SQL,
            limit=100,
            enable_log=True
        )
        
        elapsed_time = time.time() - start_time
        
        print(f"\n{'='*70}")
        print(f"✅ 查询成功!")
        print(f"Instance ID: {instance_id}")
        print(f"总耗时: {elapsed_time:.2f} 秒")
        print(f"返回行数: {len(df)}")
        
        if not df.empty:
            print(f"\n查询结果:")
            print(df.to_string(index=False))
        
        return {
            "success": True,
            "method": "run_sql_with_progress",
            "instance_id": instance_id,
            "elapsed_time": elapsed_time,
            "rows": len(df)
        }
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"\n❌ 查询失败: {e}")
        return {
            "success": False,
            "method": "run_sql_with_progress",
            "error": str(e),
            "elapsed_time": elapsed_time
        }


def test_execute_sql_with_priority(client: OdpsClient):
    """测试 execute_sql_with_priority 方法（priority 参数方式）"""
    print("\n" + "=" * 70)
    print("方法 2: execute_sql_with_priority (priority 参数方式, priority=7)")
    print("=" * 70)
    
    start_time = time.time()
    
    try:
        df, instance_id = client.execute_sql_with_priority(
            sql=TEST_SQL,
            priority=7,
            limit=100,
            enable_log=True
        )
        
        elapsed_time = time.time() - start_time
        
        print(f"\n{'='*70}")
        print(f"✅ 查询成功!")
        print(f"Instance ID: {instance_id}")
        print(f"总耗时: {elapsed_time:.2f} 秒")
        print(f"返回行数: {len(df)}")
        
        if not df.empty:
            print(f"\n查询结果:")
            print(df.to_string(index=False))
        
        return {
            "success": True,
            "method": "execute_sql_with_priority",
            "instance_id": instance_id,
            "elapsed_time": elapsed_time,
            "rows": len(df)
        }
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"\n❌ 查询失败: {e}")
        return {
            "success": False,
            "method": "execute_sql_with_priority",
            "error": str(e),
            "elapsed_time": elapsed_time
        }


def print_comparison(result1: dict, result2: dict):
    """打印对比结果"""
    print("\n" + "=" * 70)
    print("对比总结")
    print("=" * 70)
    
    print(f"\n{'方法':<35} {'状态':<10} {'耗时(秒)':<12} {'返回行数':<10}")
    print("-" * 70)
    
    for result in [result1, result2]:
        method = result["method"]
        status = "✅ 成功" if result["success"] else "❌ 失败"
        elapsed = f"{result['elapsed_time']:.2f}"
        rows = str(result.get("rows", "N/A"))
        print(f"{method:<35} {status:<10} {elapsed:<12} {rows:<10}")
    
    print("\n" + "=" * 70)
    print("技术差异对比")
    print("=" * 70)
    print("""
方法 1: run_sql_with_progress
  - 使用 hints={"odps.instance.priority": "7"} 设置优先级
  - 通过 options.sql.settings 全局配置
  - 当前 agent 默认使用此方法

方法 2: execute_sql_with_priority  
  - 使用 priority=7 参数直接设置优先级
  - 更符合 ODPS Python SDK 的标准用法
  - 优先级参数更直观，易于动态调整

注意事项:
  - 两种方法最终都调用 self.odps.execute_sql()
  - 只是传递优先级的方式不同
  - 执行效果应该是一致的
""")


def main():
    """主函数"""
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
        client = test_odps_connection()
        
        print(f"\n测试 SQL:\n{TEST_SQL}")
        
        # 测试方法 1
        result1 = test_run_sql_with_progress(client)
        
        # 等待 3 秒避免资源竞争
        print("\n等待 3 秒...")
        time.sleep(3)
        
        # 测试方法 2
        result2 = test_execute_sql_with_priority(client)
        
        # 打印对比结果
        print_comparison(result1, result2)
        
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
