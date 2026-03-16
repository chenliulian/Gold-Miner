# CVR 模型偏差分析

## 名称
analyze_cvr_pcoc

## 描述
分析 CVR 模型的预测偏差 (PCOC = pCVR / CVR)，支持 cpi/ocpc/ocpi 等转化类型。

## 输入表
依赖 build_adgroup_data 生成的中间表，字段包括：
- dld_num: 下载数 (SUM(dld_label))
- conv_num: 转化数 (根据转化类型SUM对应conv_label)
- pcvr_raw_sum: 原始 pCVR 求和 (SUM(cvr_raw))
- pcvr_sum: pCVR 求和 (SUM(cvr))
- cvr: 实际 CVR = conv_num / dld_num
- pcvr_raw: 原始预估 CVR = pcvr_raw_sum / dld_num
- pcvr: 预估 CVR = pcvr_sum / dld_num

## 参数
- input_table: 输入表名 (build_adgroup_data 输出的表)
- level: 分析维度 (可选: adgroup, pkg_buz)
- cost_types: 计费类型 (可选，如 '6,7')

## 计算逻辑
- pcoc = pcvr / cvr (pCVR / 实际CVR)
- pcoc_raw = pcvr_raw / cvr
- abs_error = |pcoc - 1|

## 输出字段
- dt: 日期
- ad_group_id / ad_package_name: 广告维度
- dld_num: 下载数
- conv_num: 转化数
- pcvr_raw_sum: 原始pCVR求和
- pcvr_sum: pCVR求和
- cvr: 实际 CVR
- pcvr_raw: 原始预估CVR
- pcvr: 预估CVR
- pcoc: CVR偏差 (1.0=准确, >1=高估, <1=低估)
- abs_error: 绝对偏差

## 转化类型
- cost_type='6' 或 '7': conv_label_active (激活)
- transform_target_cn 包含 '注册': conv_label_register
- transform_target_cn = '付费': conv_label_pay
- transform_target_cn = '首次付费': conv_label_first_pay

## 使用场景
- 评估 CVR 模型预估准确性
- 区分不同转化类型的偏差
- 优化转化出价
