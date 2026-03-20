#!/usr/bin/env python3
"""查询 ODPS 表结构并生成知识库 YAML 文件"""

import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.gold_miner.odps_client import OdpsClient, OdpsConfig
from src.gold_miner.config import Config

def query_table_schema(table_name: str):
    """查询表结构"""
    config = Config(
        llm_base_url=os.getenv("LLM_BASE_URL", ""),
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        llm_model=os.getenv("LLM_MODEL", ""),
        odps_access_id=os.getenv("ODPS_ACCESS_ID", ""),
        odps_access_key=os.getenv("ODPS_ACCESS_KEY", ""),
        odps_project=os.getenv("ODPS_PROJECT", ""),
        odps_endpoint=os.getenv("ODPS_ENDPOINT", ""),
        odps_quota=os.getenv("ODPS_QUOTA", ""),
    )

    odps_config = OdpsConfig.from_config(config)
    client = OdpsClient(odps_config)

    # 获取表结构
    table = client.odps.get_table(table_name)

    print(f"表名: {table_name}")
    print(f"注释: {table.comment}")
    print(f"\n列信息:")
    print("-" * 80)

    for col in table.schema.columns:
        print(f"  {col.name}: {col.type} - {col.comment}")

    print(f"\n分区信息:")
    print("-" * 80)
    if table.schema.partitions:
        for part in table.schema.partitions:
            print(f"  {part.name}: {part.type} - {part.comment}")
    else:
        print("  无分区")

    return table

if __name__ == "__main__":
    table_name = "com_ads.ads_creativity_filter_hi"
    query_table_schema(table_name)
