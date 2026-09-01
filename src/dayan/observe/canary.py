# -*- coding: utf-8 -*-
"""对拍探针（canary）：用训练未见过的留出随机样本问模型，再与规则引擎真值比对。
离线评估与线上巡检共用同一套逻辑：
  probes = build_probes(...)              # 造留出题目（含 engine/kw/问题/事实/标准答案）
  summary, bad = run_probes(backend, ...) # backend(system, user, gold)->answer 字符串
backend 可替换：
  echo_backend   直接返回引擎标准答案，用于自检评估器（事实命中率应为 100%）
  blank_backend  返回空串，用于对照（应为 0%）
  mlx_backend    Apple MLX 本地加载（懒加载，仅 Mac）
  openai_backend 请求 OpenAI 兼容服务（mlx_lm.server / Ollama / vLLM）
单条评估逻辑与免责判定统一在 observe.evaluation，汇总统一在 observe.metrics。
"""
import json
import random
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from ..core.registry import get_engine
from ..sft.generator import SAMPLERS, ASK, human_args
from ..sft.prompts import system_prompt
from . import facts as F
from .evaluation import DISCLAIMER_MARKS, evaluate_one, has_disclaimer  # noqa: F401


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


def check_model_url(base_url, allow_public=False):
    """模型服务地址校验：仅 http(s)；默认仅允许本机/内网地址（SSRF 防护）。"""
    u = urllib.parse.urlparse(base_url.rstrip("/"))
    if u.scheme not in ("http", "https"):
        raise ValueError(f"base_url 仅支持 http/https：{base_url}")
    if allow_public:
        return
    host = u.hostname or ""
    try:
        import ipaddress
        ip = ipaddress.ip_address(host)
        ok = ip.is_loopback or ip.is_private
    except ValueError:
        ok = host == "localhost"
    if not ok:
        raise ValueError(f"出于 SSRF 防护，默认仅允许本机/内网模型服务地址；"
                         f"公网地址请显式传 allow_public=True：{base_url}")


def openai_backend(base_url="http://127.0.0.1:8080/v1", model="local",
                   temperature=0.0, max_tokens=1024, timeout=120,
                   allow_public=False):
    check_model_url(base_url, allow_public)

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


def run_probes(backend, probes, logger=None, workers=1):
    """批量对拍：逐条（或并发 workers 路）评估，返回 (汇总指标, 坏例列表)。

    汇总直接复用 metrics.aggregate，与线上网关同一套口径；
    workers>1 时结果按探针顺序回收，落盘顺序与探针顺序一致。
    """
    from . import metrics as M

    def _one(p):
        rec, _ = evaluate_one(p["engine"], p["kw"], p["result"], p["question"],
                              p["system"], backend, logger=logger,
                              record_answer=True)
        return rec

    if workers and workers > 1:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            rows = list(ex.map(_one, probes))
    else:
        rows = [_one(p) for p in probes]
    badcases = [r for r in rows if not r["ok"] or r["missing"]]
    return M.aggregate(rows), badcases
