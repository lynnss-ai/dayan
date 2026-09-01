# -*- coding: utf-8 -*-
"""监控网关核心：规则引擎先算 → 调上游模型解读 → 事实对拍 → 留痕。
单条评估（计时/事实比对/免责检查/记录字段）统一走 observe.evaluation，
与离线对拍探针共享同一套口径。"""
from ..core.registry import get_engine
from ..sft.prompts import system_prompt
from . import metrics as M
from .evaluation import evaluate_one


def handle_chat(payload, upstream, log_path="evals/requests.jsonl"):
    """纯函数：upstream(system, user) -> answer 文本，便于无网络单测。"""
    engine = payload["engine"]
    params = payload.get("params", {})
    question = payload.get("question", "请按排盘结果解读")
    result = get_engine(engine).cast(**params)
    system = system_prompt(engine)

    def _backend(s, q, gold):
        user = (f"{q}\n\n【规则引擎排盘结果（以此为准，勿自行重算）】\n{gold}")
        return upstream(s, user)

    rec, answer = evaluate_one(engine, params, result, question, system, _backend,
                               logger=lambda r: M.log(log_path, r))
    return {"engine": engine, "answer": answer, "hit_facts": rec["hit_facts"],
            "n_facts": rec["n_facts"], "missing_facts": rec["missing"],
            "has_disclaimer": rec["has_disclaimer"],
            "latency_ms": rec["latency_ms"], "log": rec}
