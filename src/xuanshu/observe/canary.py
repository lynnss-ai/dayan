# -*- coding: utf-8 -*-
"""对拍探针（canary）：用训练未见过的留出随机样本问模型，再与规则引擎真值比对。
离线评估与线上巡检共用同一套逻辑：
  probes = build_probes(...)           # 造留出题目（含 engine/kw/问题/事实/标准答案）
  result = run_probes(backend, probes) # backend(system, user, gold)->answer 字符串
backend 可替换：
  echo_backend   直接返回引擎标准答案，用于自检评估器（事实命中率应为 100%）
  blank_backend  返回空串，用于对照（应为 0%）
  mlx_backend    Apple MLX 本地加载（懒加载，仅 Mac）
  openai_backend 请求 OpenAI 兼容服务（mlx_lm.server / Ollama / vLLM）
"""
import json
import random
import time
import urllib.request

from ..core.registry import get_engine
from ..sft.generator import SAMPLERS, ASK, human_args
from ..sft.prompts import system_prompt
from . import facts as F

DISCLAIMER_MARKS = ("参考", "不构成", "娱乐", "传统文化")


def build_probes(engines=None, n_per_engine=5, seed=999):
    """留出集：seed 默认 999，与训练 seed(42) 错开，保证不是背答案。"""
    engines = engines or list(SAMPLERS.keys())
    rng = random.Random(seed)
    probes = []
    for key in engines:
        for _ in range(n_per_engine):
            kw = SAMPLERS[key](rng)
            result = get_engine(key).cast(**kw)
            q = rng.choice(ASK[key]).format(a=human_args(key, kw))
            probes.append({
                "engine": key, "kw": kw, "question": q,
                "system": system_prompt(key),
                "facts": F.expected_facts(key, kw, result),
                "gold": result["text"], "result": result})
    return probes


# ---------- backends ----------
def echo_backend(system, user, gold):
    return gold


def blank_backend(system, user, gold):
    return ""


def openai_backend(base_url="http://127.0.0.1:8080/v1", model="local",
                   temperature=0.0, max_tokens=1024, timeout=120):
    def _call(system, user, gold):
        body = json.dumps({
            "model": model, "temperature": temperature, "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}]}).encode("utf-8")
        req = urllib.request.Request(base_url.rstrip("/") + "/chat/completions",
                                     data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]
    return _call


def mlx_backend(model_path, max_tokens=1024):
    from mlx_lm import load, generate  # 懒加载，仅 Apple Silicon
    model, tokenizer = load(model_path)

    def _call(system, user, gold):
        msgs = [{"role": "system", "content": system},
                {"role": "user", "content": user}]
        try:
            prompt = tokenizer.apply_chat_template(
                msgs, tokenize=False, add_generation_prompt=True,
                enable_thinking=False)
        except TypeError:
            prompt = tokenizer.apply_chat_template(
                msgs, tokenize=False, add_generation_prompt=True)
        return generate(model, tokenizer, prompt=prompt, max_tokens=max_tokens,
                        verbose=False)
    return _call


def has_disclaimer(text):
    return any(m in text for m in DISCLAIMER_MARKS)


def run_probes(backend, probes, logger=None):
    rows, badcases = [], []
    for p in probes:
        t0 = time.time()
        try:
            ans = backend(p["system"], p["question"], p["gold"])
            ok, err = True, ""
        except Exception as e:  # noqa: BLE001
            ans, ok, err = "", False, repr(e)
        lat = round((time.time() - t0) * 1000, 1)
        hit, tot, missing = F.check_answer(p["engine"], p["kw"], p["result"], ans)
        rec = {"engine": p["engine"], "ok": ok, "err": err,
               "latency_ms": lat, "hit_facts": hit, "n_facts": tot,
               "full_match": tot > 0 and hit == tot,
               "has_disclaimer": has_disclaimer(ans),
               "question": p["question"], "missing": missing,
               "answer": ans if not ok or missing else ""}
        rows.append(rec)
        if logger:
            logger({"engine": p["engine"], "ok": ok, "latency_ms": lat,
                    "hit_facts": hit, "n_facts": tot,
                    "has_disclaimer": rec["has_disclaimer"],
                    "flagged": bool(err) or (tot > 0 and hit < tot),
                    "note": err})
        if not ok or missing:
            badcases.append(rec)
    return summarize(rows), badcases


def summarize(rows):
    n = len(rows)
    fact_tot = sum(r["n_facts"] for r in rows)
    fact_hit = sum(r["hit_facts"] for r in rows)
    return {
        "n": n, "ok_rate": round(sum(r["ok"] for r in rows) / n, 4) if n else 0,
        "fact_hit_rate": round(fact_hit / fact_tot, 4) if fact_tot else None,
        "full_match_rate": round(sum(r["full_match"] for r in rows) / n, 4) if n else 0,
        "disclaimer_rate": round(sum(r["has_disclaimer"] for r in rows) / n, 4) if n else 0,
        "p95_ms": round(_p95([r["latency_ms"] for r in rows]), 1),
        "by_engine": _by_engine(rows)}


def _p95(xs):
    if not xs:
        return 0
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(0.95 * (len(xs) - 1))))]


def _by_engine(rows):
    out = {}
    for r in rows:
        b = out.setdefault(r["engine"], {"n": 0, "hit": 0, "tot": 0, "full": 0})
        b["n"] += 1
        b["hit"] += r["hit_facts"]
        b["tot"] += r["n_facts"]
        b["full"] += int(r["full_match"])
    for b in out.values():
        b["fact_hit_rate"] = round(b["hit"] / b["tot"], 4) if b["tot"] else None
        b["full_match_rate"] = round(b["full"] / b["n"], 4)
    return out
