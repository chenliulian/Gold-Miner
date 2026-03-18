#!/usr/bin/env python3
"""
测试 DESC 命令返回格式
"""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from dotenv import load_dotenv
from gold_miner.odps_client import OdpsClient, OdpsConfig
from gold_miner.config import Config

load_dotenv()

def test_desc():
    config = Config.from_env()
    odps_config = OdpsConfig.from_config(config)
    client = OdpsClient(odps_config)
    
    table_name = "com_ads.ads_tracker_ad_cpc_cost_di"
    
    print("=" * 60)
    print(f"测试 DESC {table_name}")
    print("=" * 60)
    
    desc_sql = f"DESC {table_name}"
    df = client.run_sql(desc_sql, enable_log=True)
    
    print(f"\n返回行数: {len(df)}")
    print(f"返回列数: {len(df.columns)}")
    print(f"列名: {list(df.columns)}")
    print(f"\n原始数据:")
    print(df.to_string())
    
    # 也测试 DESC EXTENDED
    print("\n" + "=" * 60)
    print(f"测试 DESC EXTENDED {table_name}")
    print("=" * 60)
    
    desc_ext_sql = f"DESC EXTENDED {table_name}"
    df2 = client.run_sql(desc_ext_sql, enable_log=True)
    
    print(f"\n返回行数: {len(df2)}")
    print(f"返回列数: {len(df2.columns)}")
    print(f"列名: {list(df2.columns)}")
    print(f"\n原始数据 (前20行):")
    print(df2.head(20).to_string())

if __name__ == "__main__":
    test_desc()
