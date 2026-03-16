# 创建新 Skill

## 名称
create_skill

## 描述
根据分析任务自动创建新的 Skill，沉淀为可复用的代码模块。

## 参数
- skill_name: Skill 名称 (英文)
- skill_description: Skill 描述
- code_template: 代码模板 (Python)
- category: 分类 (可选: maxcompute-sql, data-analysis, notification, utility)

## 使用场景

### 1. 创建数据分析 Skill
```json
{
  "skill_name": "calc_roi",
  "skill_description": "计算广告投放 ROI",
  "code_template": "def run(dataframe): ...",
  "category": "data-analysis"
}
```

### 2. 创建数据处理 Skill
```json
{
  "skill_name": "data_cleanup",
  "skill_description": "清洗异常数据",
  "code_template": "def run(df): ...",
  "category": "data-analysis"
}
```

## 输出
返回创建的 Skill 路径和代码。

## 注意事项
- Skill 名称必须唯一
- 代码模板需要是有效的 Python 代码
- 会在 skills/ 目录下创建对应文件
