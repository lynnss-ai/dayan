# -*- coding: utf-8 -*-
import json
import os
import tempfile

from xuanshu.sft import generator as gen
from xuanshu.core.registry import REGISTRY


def test_all_engines_registered():
    assert len(REGISTRY) == 16


def test_generate_structure():
    with tempfile.TemporaryDirectory() as d:
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


def test_every_sampler_runs():
    import random
    rng = random.Random(7)
    for key, fn in gen.SAMPLERS.items():
        kw = fn(rng)
        out = REGISTRY[key].cast(**kw)
        assert out.get("text")
