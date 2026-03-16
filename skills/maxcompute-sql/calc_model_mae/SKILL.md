# 模型 MAE 计算

## 名称
calc_model_mae

## 描述
计算模型预测的平均绝对误差 (MAE)。

## 前提条件
需要先运行 analyze_ctr_pcoc 和 analyze_cvr_pcoc 技能。

## 参数
- ctr_table: CTR 分析结果表
- cvr_table: CVR 分析结果表

## 输出
- ctr_mae: CTR 模型 MAE
- cvr_mae: CVR 模型 MAE

## 使用场景
- 模型效果评估
- 模型迭代参考
