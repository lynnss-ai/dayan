# -*- coding: utf-8 -*-
"""请求级指标：落 JSONL 日志，并聚合为可巡检/可出日报的统计。
每条记录字段：
  ts, engine, latency_ms, ok, n_facts, hit_facts,
  has_disclaimer, flagged, note
"""
import json
import os
import statistics
from datetime import datetime


def log(path, record):
    rec = {"ts": datetime.now().isoformat(timespec="seconds")}
    rec.update(record)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def load(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def percentile(xs, q):
    if not xs:
        return 0.0
    xs = sorted(xs)
    i = (len(xs) - 1) * q
    lo, hi = int(i), min(int(i) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def aggregate(rows):
    n = len(rows)
    if not n:
        return {"total": 0}
    lat = [r.get("latency_ms", 0) for r in rows if r.get("ok")]
    fact_tot = sum(r.get("n_facts", 0) for r in rows)
    fact_hit = sum(r.get("hit_facts", 0) for r in rows)
    full = sum(1 for r in rows
               if r.get("n_facts", 0) > 0 and r.get("hit_facts") == r.get("n_facts"))
    n_with_facts = sum(1 for r in rows if r.get("n_facts", 0) > 0)
    disc = sum(1 for r in rows if r.get("has_disclaimer"))
    flagged = sum(1 for r in rows if r.get("flagged"))
    by_engine = {}
    for r in rows:
        e = r.get("engine", "?")
        b = by_engine.setdefault(e, {"n": 0, "fact_tot": 0, "fact_hit": 0,
                                     "full": 0, "lat": []})
        b["n"] += 1
        b["fact_tot"] += r.get("n_facts", 0)
        b["fact_hit"] += r.get("hit_facts", 0)
        if r.get("n_facts", 0) > 0 and r.get("hit_facts") == r.get("n_facts"):
            b["full"] += 1
        if r.get("ok"):
            b["lat"].append(r.get("latency_ms", 0))
    for e, b in by_engine.items():
        b["fact_hit_rate"] = round(b["fact_hit"] / b["fact_tot"], 4) if b["fact_tot"] else None
        b["full_match_rate"] = round(b["full"] / b["n"], 4)
        b["p50_ms"] = round(percentile(b["lat"], 0.5), 1)
        b["p95_ms"] = round(percentile(b["lat"], 0.95), 1)
        del b["lat"]
    return {
        "total": n,
        "time_from": rows[0].get("ts"), "time_to": rows[-1].get("ts"),
        "fact_hit_rate": round(fact_hit / fact_tot, 4) if fact_tot else None,
        "full_match_rate": round(full / n_with_facts, 4) if n_with_facts else None,
        "disclaimer_rate": round(disc / n, 4),
        "flagged_rate": round(flagged / n, 4),
        "latency_p50_ms": round(percentile(lat, 0.5), 1),
        "latency_p95_ms": round(percentile(lat, 0.95), 1),
        "by_engine": by_engine}


def render_markdown(agg):
    if not agg.get("total"):
        return "# 监控日报\n\n（暂无日志记录）\n"
    L = ["# 大衍模型监控日报",
         f"\n区间：{agg['time_from']} → {agg['time_to']}，共 {agg['total']} 次请求\n",
         "| 指标 | 数值 |", "|---|---|",
         f"| 确定性事实命中率 | {agg['fact_hit_rate']} |",
         f"| 全事实答对率(全对才算) | {agg['full_match_rate']} |",
         f"| 免责声明覆盖率 | {agg['disclaimer_rate']} |",
         f"| 越界/异常标记率 | {agg['flagged_rate']} |",
         f"| 延迟 P50/P95 (ms) | {agg['latency_p50_ms']} / {agg['latency_p95_ms']} |",
         "\n## 分术数\n",
         "| 引擎 | 次数 | 事实命中率 | 全对率 | P50 | P95 |",
         "|---|---|---|---|---|---|"]
    for e, b in sorted(agg["by_engine"].items()):
        L.append(f"| {e} | {b['n']} | {b['fact_hit_rate']} | {b['full_match_rate']} "
                 f"| {b['p50_ms']} | {b['p95_ms']} |")
    return "\n".join(L) + "\n"
