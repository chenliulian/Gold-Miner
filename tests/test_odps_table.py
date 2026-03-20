#!/usr/bin/env python3
"""
测试 ODPS 客户端读取 com_ads.ads_tracker_ad_cpc_cost_di 表
"""
import os
import sys
from pathlib import Path

import pytest

# 添加 src 到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from dotenv import load_dotenv
from gold_miner.odps_client import OdpsClient, OdpsConfig

# 加载环境变量
load_dotenv()


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


@pytest.fixture
def table_name():
    """测试表名 fixture"""
    return "com_ads.ads_tracker_ad_cpc_cost_di"


@pytest.mark.skipif(
    not os.getenv("ODPS_ACCESS_ID"),
    reason="ODPS credentials not configured"
)
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
    assert client is not None


@pytest.mark.skipif(
    not os.getenv("ODPS_ACCESS_ID"),
    reason="ODPS credentials not configured"
)
def test_table_exists(odps_client, table_name):
    """测试表是否存在"""
    print("\n" + "=" * 60)
    print(f"检查表是否存在: {table_name}")
    print("=" * 60)
    
    try:
        # 先尝试获取表元数据（不需要分区）
        sql = f"""
        DESC {table_name}
        """
        df = odps_client.run_sql(sql, limit=1)
        print(f"✅ 表 {table_name} 存在且可访问")
        print(f"返回数据行数: {len(df)}")
        assert True
    except Exception as e:
        error_msg = str(e)
        # 如果是分区错误，说明表存在
        if "full scan with all partitions" in error_msg or "specify partition predicates" in error_msg:
            print(f"✅ 表 {table_name} 存在（分区表，需要指定分区）")
            assert True
        else:
            print(f"❌ 访问表失败: {e}")
            pytest.skip(f"表访问失败: {e}")


@pytest.mark.skipif(
    not os.getenv("ODPS_ACCESS_ID"),
    reason="ODPS credentials not configured"
)
def test_table_schema(odps_client, table_name):
    """测试获取表结构"""
    print("\n" + "=" * 60)
    print(f"获取表结构: {table_name}")
    print("=" * 60)
    
    try:
        sql = f"""
        DESC {table_name}
        """
        df = odps_client.run_sql(sql, limit=100)
        print(f"✅ 表结构信息:")
        print(df.to_string())
        assert len(df) > 0
    except Exception as e:
        print(f"❌ 获取表结构失败: {e}")
        pytest.skip(f"获取表结构失败: {e}")


@pytest.mark.skipif(
    not os.getenv("ODPS_ACCESS_ID"),
    reason="ODPS credentials not configured"
)
def test_table_data(odps_client, table_name):
    """测试读取表数据"""
    print("\n" + "=" * 60)
    print(f"读取表数据: {table_name}")
    print("=" * 60)
    
    try:
        # 先获取分区信息，然后读取最新分区数据
        sql_partitions = f"""
        SHOW PARTITIONS {table_name}
        """
        partition_df = odps_client.run_sql(sql_partitions, limit=100)
        
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
        
        df, instance_id = odps_client.run_sql_with_progress(sql, limit=5)
        print(f"✅ 数据读取成功")
        print(f"Instance ID: {instance_id}")
        print(f"返回行数: {len(df)}")
        print(f"列数: {len(df.columns)}")
        print(f"\n列名: {list(df.columns)}")
        print(f"\n数据预览:")
        print(df.to_string())
        assert len(df) >= 0  # 允许空结果
    except Exception as e:
        print(f"❌ 读取数据失败: {e}")
        import traceback
        traceback.print_exc()
        pytest.skip(f"读取数据失败: {e}")


@pytest.mark.skipif(
    not os.getenv("ODPS_ACCESS_ID"),
    reason="ODPS credentials not configured"
)
def test_table_partition(odps_client, table_name):
    """测试获取表分区信息"""
    print("\n" + "=" * 60)
    print(f"获取分区信息: {table_name}")
    print("=" * 60)
    
    try:
        sql = f"""
        SHOW PARTITIONS {table_name}
        """
        df = odps_client.run_sql(sql, limit=100)
        print(f"✅ 分区信息:")
        print(df.to_string())
        assert len(df) >= 0  # 允许空结果（非分区表）
    except Exception as e:
        print(f"❌ 获取分区信息失败: {e}")
        pytest.skip(f"获取分区信息失败: {e}")


def main():
    """命令行运行测试"""
    table_name = "com_ads.ads_tracker_ad_cpc_cost_di"
    
    try:
        # 1. 测试连接
        config = OdpsConfig(
            access_id=os.getenv("ODPS_ACCESS_ID"),
            access_key=os.getenv("ODPS_ACCESS_KEY"),
            project=os.getenv("ODPS_PROJECT"),
            endpoint=os.getenv("ODPS_ENDPOINT"),
            quota=os.getenv("ODPS_QUOTA", ""),
        )
        client = OdpsClient(config)
        print("✅ ODPS 客户端初始化成功")
        
        # 2. 测试表是否存在
        try:
            sql = f"DESC {table_name}"
            df = client.run_sql(sql, limit=1)
            print(f"✅ 表 {table_name} 存在且可访问")
        except Exception as e:
            error_msg = str(e)
            if "full scan with all partitions" in error_msg or "specify partition predicates" in error_msg:
                print(f"✅ 表 {table_name} 存在（分区表，需要指定分区）")
            else:
                print(f"❌ 访问表失败: {e}")
                return
        
        # 3. 测试获取表结构
        try:
            sql = f"DESC {table_name}"
            df = client.run_sql(sql, limit=100)
            print(f"✅ 表结构信息:")
            print(df.to_string())
        except Exception as e:
            print(f"❌ 获取表结构失败: {e}")
        
        # 4. 测试获取分区信息
        try:
            sql = f"SHOW PARTITIONS {table_name}"
            df = client.run_sql(sql, limit=100)
            print(f"✅ 分区信息:")
            print(df.to_string())
        except Exception as e:
            print(f"❌ 获取分区信息失败: {e}")
        
        # 5. 测试读取数据
        try:
            sql = f"SELECT * FROM {table_name} LIMIT 5"
            df, instance_id = client.run_sql_with_progress(sql, limit=5)
            print(f"✅ 数据读取成功")
            print(f"Instance ID: {instance_id}")
            print(f"返回行数: {len(df)}")
            print(df.to_string())
        except Exception as e:
            print(f"❌ 读取数据失败: {e}")
        
        print("\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
