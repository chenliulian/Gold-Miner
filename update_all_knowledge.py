#!/usr/bin/env python3
"""
批量更新 knowledge/tables 目录中所有表的 YAML 文件
"""
import sys
sys.path.insert(0, 'src')
sys.path.insert(0, 'skills')

from dotenv import load_dotenv
load_dotenv()

from pathlib import Path
import yaml
from explore_table.explore_table import run


def get_table_name_from_yaml(yaml_file: Path) -> str:
    """从 YAML 文件中读取表名"""
    try:
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # 优先使用基本信息中的表名
        if data and '基本信息' in data:
            table_name = data['基本信息'].get('表名', '')
            if table_name:
                return table_name
        
        # 备选：从文件名推断
        filename = yaml_file.name.replace('.yaml', '')
        # 替换 _ 为 . 来得到项目名和表名
        parts = filename.split('_', 1)
        if len(parts) == 2:
            # 尝试识别项目名
            if parts[0] in ['mi', 'com', 'ads']:
                # 更复杂的项目名解析
                if 'ads_strategy' in filename:
                    return filename.replace('ads_strategy_', 'ads_strategy.')
                elif 'com_ads' in filename:
                    return filename.replace('com_ads_', 'com_ads.')
                elif 'mi_ads_dmp_dev' in filename:
                    return filename.replace('mi_ads_dmp_dev_', 'mi_ads_dmp_dev.')
                elif 'mi_ads_dmp' in filename:
                    return filename.replace('mi_ads_dmp_', 'mi_ads_dmp.')
    except Exception as e:
        print(f"  读取 YAML 失败: {e}")
    
    # 如果都失败了，返回文件名作为备选
    return yaml_file.name.replace('.yaml', '').replace('_', '.', 1)


def main():
    knowledge_dir = Path("/Users/shmichenliulian/GoldMiner/knowledge/tables")

    # 获取所有 yaml 文件
    yaml_files = list(knowledge_dir.glob("*.yaml"))

    print(f"找到 {len(yaml_files)} 个知识文件需要更新")
    print("=" * 60)

    success_count = 0
    failed_count = 0

    for yaml_file in sorted(yaml_files):
        full_table_name = get_table_name_from_yaml(yaml_file)

        print(f"\n更新: {full_table_name}")
        print("-" * 60)

        try:
            result = run(
                table_name=full_table_name,
                sample_rows=3,
                sample_date="20260317",
                generate_knowledge=True,
            )

            if 'knowledge_generation' in result:
                kg = result['knowledge_generation']
                if kg.get('success'):
                    details = kg.get('details', {})
                    updated = details.get('updated_comments', 0)
                    added = details.get('added_fields', 0)
                    total = details.get('total_fields', 0)
                    print(f"  ✓ 成功: 更新 {updated} 个注释, 添加 {added} 个字段, 总共 {total} 个字段")
                    success_count += 1
                else:
                    print(f"  ✗ 失败: {kg.get('error', '未知错误')}")
                    failed_count += 1
            else:
                print(f"  ✗ 失败: 未返回知识生成结果")
                failed_count += 1

        except Exception as e:
            print(f"  ✗ 异常: {str(e)}")
            failed_count += 1

    print("\n" + "=" * 60)
    print(f"更新完成: 成功 {success_count} 个, 失败 {failed_count} 个")


if __name__ == "__main__":
    main()
