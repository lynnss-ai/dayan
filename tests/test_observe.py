# -*- coding: utf-8 -*-
import json
import os
import tempfile

from dayan.observe import canary, metrics as M, facts as F


def test_fact_extractors_self_consistent():
    """用引擎标准答案自问自答，所有确定性事实必须 100% 命中（验证事实选取无误）。"""
    probes = canary.build_probes(n_per_engine=3, seed=999)
    summary, bad = canary.run_probes(canary.echo_backend, probes)
    assert summary["n"] == 48
    assert summary["fact_hit_rate"] == 1.0, [(b["engine"], b["missing"]) for b in bad]
    assert summary["full_match_rate"] == 1.0


def test_blank_scores_zero():
    probes = canary.build_probes(engines=["bazi", "meihua"], n_per_engine=2, seed=7)
    summary, bad = canary.run_probes(canary.blank_backend, probes)
    assert summary["fact_hit_rate"] == 0.0
    assert len(bad) == len(probes)


def test_holdout_differs_from_training_seed():
    a = canary.build_probes(engines=["bazi"], n_per_engine=5, seed=42)
    b = canary.build_probes(engines=["bazi"], n_per_engine=5, seed=999)
    qa = [x["question"] for x in a]
    qb = [x["question"] for x in b]
    assert qa != qb  # 评估留出集与训练随机种子错开


def test_metrics_aggregate_and_log():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "req.jsonl")
        for i in range(4):
            M.log(path, {"engine": "bazi", "ok": True, "latency_ms": 100 + i * 50,
                         "n_facts": 4, "hit_facts": 4 if i else 2,
                         "has_disclaimer": True, "flagged": i == 0})
        rows = M.load(path)
        agg = M.aggregate(rows)
        assert agg["total"] == 4
        assert agg["by_engine"]["bazi"]["full"] == 3
        assert agg["latency_p95_ms"] >= agg["latency_p50_ms"]
        md = M.render_markdown(agg)
        assert "确定性事实命中率" in md


def test_norm_ignores_spaces():
    assert F.norm("天 格 19") == "天格19"


def test_monitored_gateway_core():
    import tempfile
    from dayan.observe.gateway import handle_chat
    with tempfile.TemporaryDirectory() as d:
        logp = os.path.join(d, "req.jsonl")
        # 假上游：把引擎给的盘原样复述并加参考语（模拟答对）
        out = handle_chat(
            {"engine": "bazi",
             "params": {"year": 1990, "month": 3, "day": 15, "hour": 12, "gender": "male"},
             "question": "解读一下"},
            upstream=lambda s, u: u + "\n以上为传统文化参考。",
            log_path=logp)
        assert out["n_facts"] == 4 and out["hit_facts"] == 4
        assert out["has_disclaimer"] and out["missing_facts"] == []
        rows = M.load(logp)
        assert len(rows) == 1 and rows[0]["flagged"] is False
