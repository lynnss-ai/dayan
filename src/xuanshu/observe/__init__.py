# -*- coding: utf-8 -*-
"""玄枢 observe —— 训练后验证与线上监控。
- facts：从规则引擎的结构化结果里抽取"模型答案必须包含的确定性事实"。
- metrics：请求级指标落 JSONL，并聚合为命中率/延迟分位/合规率。
- canary：用留出样本对模型做"对拍探针"，离线评估与线上巡检共用。
"""
from . import facts, metrics, canary  # noqa: F401
