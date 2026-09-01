# -*- coding: utf-8 -*-
"""监控网关核心：规则引擎先算 → 调上游模型解读 → 事实对拍 → 留痕。"""
import time

from ..core.registry import get_engine
from ..sft.prompts import system_prompt
from . import facts as F
from . import canary
from . import metrics as M


def handle_chat(payload, upstream, log_path="evals/requests.jsonl"):
    """纯函数：upstream(system, user) -> answer 文本，便于无网络单测。"""
    engine = payload["engine"]
    params = payload.get("params", {})
    question = payload.get("question", "请按排盘结果解读")
    result = get_engine(engine).cast(**params)
    system = system_prompt(engine)
    user = (f"{question}\n\n【规则引擎排盘结果（以此为准，勿自行重算）】\n"
            f"{result['text']}")
    t0 = time.time()
    answer = upstream(system, user)
    latency = round((time.time() - t0) * 1000, 1)
    hit, tot, missing = F.check_answer(engine, params, result, answer)
    disc = canary.has_disclaimer(answer)
    rec = M.log(log_path, {
        "engine": engine, "ok": True, "latency_ms": latency,
        "hit_facts": hit, "n_facts": tot, "has_disclaimer": disc,
        "flagged": tot > 0 and hit < tot,
        "note": "事实缺失:" + ",".join(missing) if missing else ""})
    return {"engine": engine, "answer": answer, "hit_facts": hit, "n_facts": tot,
            "missing_facts": missing, "has_disclaimer": disc,
            "latency_ms": latency, "log": rec}
