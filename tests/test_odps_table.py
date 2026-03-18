#!/usr/bin/env python3
"""
测试 ODPS 客户端读取 com_ads.ads_tracker_ad_cpc_cost_di 表
"""
import os
import sys
from pathlib import Path

# 添加 src 到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from dotenv import load_dotenv
from gold_miner.odps_client import OdpsClient, OdpsConfig

# 加载环境变量
load_dotenv()

def test_odps_connection():
    """测试 ODPS 连接"""
    print("=" * 60)
    print("测试 ODPS 连接")
    print("=" * 60)
    
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

def test_table_exists(client: OdpsClient, table_name: str):
    """测试表是否存在"""
    print("\n" + "=" * 60)
    print(f"检查表是否存在: {table_name}")
    print("=" * 60)
    
    try:
        # 先尝试获取表元数据（不需要分区）
        sql = f"""
        DESC {table_name}
        """
        df = client.run_sql(sql, limit=1)
        print(f"✅ 表 {table_name} 存在且可访问")
        print(f"返回数据行数: {len(df)}")
        return True
    except Exception as e:
        error_msg = str(e)
        # 如果是分区错误，说明表存在
        if "full scan with all partitions" in error_msg or "specify partition predicates" in error_msg:
            print(f"✅ 表 {table_name} 存在（分区表，需要指定分区）")
            return True
        print(f"❌ 访问表失败: {e}")
        return False

def test_table_schema(client: OdpsClient, table_name: str):
    """测试获取表结构"""
    print("\n" + "=" * 60)
    print(f"获取表结构: {table_name}")
    print("=" * 60)
    
    try:
        sql = f"""
        DESC {table_name}
        """
        df = client.run_sql(sql, limit=100)
        print(f"✅ 表结构信息:")
        print(df.to_string())
        return df
    except Exception as e:
        print(f"❌ 获取表结构失败: {e}")
        return None

def test_table_data(client: OdpsClient, table_name: str):
    """测试读取表数据"""
    print("\n" + "=" * 60)
    print(f"读取表数据: {table_name}")
    print("=" * 60)
    
    try:
        # 先获取分区信息，然后读取最新分区数据
        sql_partitions = f"""
        SHOW PARTITIONS {table_name}
        """
        partition_df = client.run_sql(sql_partitions, limit=100)
        
        if len(partition_df) == 0:
            print("⚠️ 表没有分区，尝试直接读取")
            sql = f"""
            SELECT *
            FROM {table_name}
            LIMIT 5
            """
        else:
            # 获取最新分区
            partitions = partition_df.iloc[:, 0].tolist()
            latest_partition = partitions[-1]  # 通常最后一个是最新的
            print(f"找到 {len(partitions)} 个分区，使用: {latest_partition}")
            
            # 解析分区字段和值（格式如：dt=20220411）
            partition_parts = latest_partition.split('=')
            if len(partition_parts) == 2:
                partition_col = partition_parts[0]
                partition_val = partition_parts[1]
            else:
                partition_col = 'dt'
                partition_val = latest_partition.replace('dt=', '')
            
            print(f"使用分区字段: {partition_col} = {partition_val}")
            
            sql = f"""
            SELECT *
            FROM {table_name}
            WHERE {partition_col} = '{partition_val}'
            LIMIT 5
            """
        
        df, instance_id = client.run_sql_with_progress(sql, limit=5)
        print(f"✅ 数据读取成功")
        print(f"Instance ID: {instance_id}")
        print(f"返回行数: {len(df)}")
        print(f"列数: {len(df.columns)}")
        print(f"\n列名: {list(df.columns)}")
        print(f"\n数据预览:")
        print(df.to_string())
        return df
    except Exception as e:
        print(f"❌ 读取数据失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_table_partition(client: OdpsClient, table_name: str):
    """测试获取表分区信息"""
    print("\n" + "=" * 60)
    print(f"获取分区信息: {table_name}")
    print("=" * 60)
    
    try:
        sql = f"""
        SHOW PARTITIONS {table_name}
        """
        df = client.run_sql(sql, limit=100)
        print(f"✅ 分区信息:")
        print(df.to_string())
        return df
    except Exception as e:
        print(f"❌ 获取分区信息失败: {e}")
        return None

def main():
    table_name = "com_ads.ads_tracker_ad_cpc_cost_di"
    
    try:
        # 1. 测试连接
        client = test_odps_connection()
        
        # 2. 测试表是否存在
        if not test_table_exists(client, table_name):
            print(f"\n❌ 表 {table_name} 不存在或无法访问")
            return
        
        # 3. 测试获取表结构
        schema_df = test_table_schema(client, table_name)
        
        # 4. 测试获取分区信息
        partition_df = test_table_partition(client, table_name)
        
        # 5. 测试读取数据
        data_df = test_table_data(client, table_name)
        
        print("\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
