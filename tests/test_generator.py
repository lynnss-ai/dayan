# -*- coding: utf-8 -*-
import json
import os

from dayan.sft import generator as gen
from dayan.core.registry import REGISTRY


def test_all_engines_registered():
    assert len(REGISTRY) == 16


def test_generate_structure(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # generate 限制输出必须位于工作目录内
    d = "data"
    n_tr, n_va, counts = gen.generate(
        domains=["bazi", "meihua", "tarot"], per_domain=6,
        seed=1, val_ratio=0.2, outdir=d, tool_ratio=0.5)
    assert n_tr + n_va == 18 and n_va == 3
    for fn in ("sft_train.jsonl", "sft_val.jsonl"):
        path = os.path.join(d, fn)
        assert os.path.exists(path)
        with open(path, encoding="utf-8") as f:
            rows = [json.loads(x) for x in f if x.strip()]
        for r in rows:
            assert r["engine"] in ("bazi", "meihua", "tarot")
            msgs = r["messages"]
            assert msgs[0]["role"] == "system"
            assert msgs[-1]["role"] == "assistant" and msgs[-1]["content"]
            if r["kind"] == "tool_call":
                assert msgs[1]["role"] == "user" and msgs[2]["tool_calls"]

