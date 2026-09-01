# -*- coding: utf-8 -*-
"""单次评估的统一入口：对拍探针（canary）与监控网关（gateway）共用，
保证"计时→事实比对→免责检查→落盘"只有一套实现、一套指标口径。"""
import time

from . import facts as F

# 免责声明判定关键词（命中任意即视为已覆盖）
DISCLAIMER_MARKS = ("参考", "不构成", "娱乐", "传统文化")


def has_disclaimer(text: str) -> bool:
    return any(m in text for m in DISCLAIMER_MARKS)


def evaluate_one(engine: str, kw: dict, result: dict, question: str, system: str,
                 backend, logger=None, record_answer: bool = False):
    """跑一次"模型回答→事实对拍→免责检查→落盘"。

    backend(system, question, gold) -> answer 字符串；gold 为引擎标准答案文本。
    网关场景由调用方包一层适配器把排盘结果拼进 user 消息。
    返回 (统一 schema 的记录, answer)；记录字段与 metrics.aggregate 对齐。
    """
    t0 = time.time()
    try:
        answer = backend(system, question, result["text"])
        ok, err = True, ""
    except Exception as e:  # noqa: BLE001
        answer, ok, err = "", False, repr(e)
    latency = round((time.time() - t0) * 1000, 1)
    hit, tot, missing = F.check_answer(engine, kw, result, answer)
    rec = {"engine": engine, "ok": ok, "latency_ms": latency,
           "hit_facts": hit, "n_facts": tot,
           "has_disclaimer": has_disclaimer(answer),
           "flagged": bool(err) or (tot > 0 and hit < tot),
           "note": err or ("事实缺失:" + ",".join(missing) if missing else ""),
           "question": question, "missing": missing}
    if record_answer:
        rec["answer"] = answer
    if logger:
        logger(rec)
    return rec, answer
