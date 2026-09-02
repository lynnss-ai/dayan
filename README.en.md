<div align="center">

# 大衍 dayan

**Deterministic Rule Engines for Divination Arts + a Metaphysics SFT Data Factory**

*"The number of the Great Expansion is fifty, of which forty-nine are used." — I Ching, Great Appendix*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](pyproject.toml)
[![Tests](https://img.shields.io/badge/tests-39%20passed-brightgreen.svg)](tests)
[![Engines](https://img.shields.io/badge/engines-16-9B59B6.svg)](#2-engine-overview)

[简体中文](README.md) | **English**

</div>

---

## What is this

A metaphysics-domain engineering project for private fine-tuning of **Qwen3.8-27B / Qwen3**. The core idea in one sentence:

> **All deterministic "chart casting / hexagram casting / arrangement" is handled by auditable rule engines; the model only learns expression and interpretation.**
> The same input always yields the same chart — the model never "miscalculates" a Ganzhi combination, hexagram line, or star placement.

In three bullets:

- **16 divination engines**: BaZi, Zi Wei Dou Shu, Qi Men, Liu Yao, Tarot, and more — one registry, one CLI, one SFT pipeline. Pure Python: reproducible, unit-tested, auditable.
- **Data factory**: every deterministic answer is computed live by the engines (including ~40% tool-call samples). Nothing hand-written, nothing fabricated.
- **Verification loop**: holdout canary probes, a monitored production gateway, and daily metrics — `fact_hit_rate` directly measures whether the model got the deterministic facts right.

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Cast a BaZi chart
dayan cast bazi year=1990 month=3 day=15 hour=12 gender=male

# Smoke-test all 16 engines + run the unit tests
dayan selftest && pytest -q

# Batch-generate multiverse SFT data (40% tool-call samples by default)
dayan generate --per-domain 40 --outdir data
```

As a library:

```python
import dayan
chart = dayan.cast("bazi", year=1990, month=3, day=15, hour=12, gender="male")
print(chart["text"])
```

## 2. Engine Overview

| key | Art | Tier | Maturity | Deterministic output |
|---|---|---|---|---|
| `bazi` | Four Pillars (BaZi) | A | complete | Four pillars, hidden stems & ten gods, NaYin, five-element strength, clashes/harms/combos, symbolic stars, luck pillars, annual pillars |
| `almanac` | Chinese Almanac | S | complete | 12 day officers, yellow/black path, 28 lunar mansions, do/don't, clashes, Peng Zu taboos, 12 hours |
| `name` | Name Five Grids | S | complete | Heaven/earth/human/outer/total grids, 81 numerology, three-talent elements (Kangxi strokes) |
| `meihua` | Plum Blossom Numerology | S | complete | Time/number casting, original-changing hexagrams, body-use relations |
| `numerology` | Life Path Numbers | S | complete | Life path, talent numbers, master numbers |
| `bazhai` | Eight Mansions Feng Shui | S | complete | Life gua, East/West four groups, eight-direction auspiciousness |
| `zhouyi` | Zhouyi Hexagrams | S | complete | Palace, shi/ying lines, inverse/opposite/nuclear/changed hexagrams |
| `xuankong` | Xuan Kong Flying Stars | A | complete | Three periods nine cycles, chart casting for period/mountain/facing stars |
| `liuyao` | Liu Yao Na Jia | A | core | Hexagram assembly, na jia, shi/ying, six relatives & six animals, void (xun kong), changed hexagram (interpretation left to the model) |
| `ziwei` | Zi Wei Dou Shu | A | core | Life/body palaces, five-element bureau, 14 major stars, 6 auspicious stars + Lu Cun/Qing Yang/Tuo Luo, four transformations, major limits |
| `qimen` | Qi Men Dun Jia | A | core | Auto ju resolution via Chai Bu (or manual dun/ju) + hour pillar; heaven/earth plates, nine stars, eight doors, eight gods, duty star & door |
| `liuren` | Da Liu Ren | A | partial | Jiang-over-hour heaven/earth plate, four lessons (three transmissions left as an interface) |
| `astrology` | Western Astrology | A | rules | Elements & modalities, aspect orbs, house rulers (planet positions need pyswisseph/upstream) |
| `physiognomy` | Face & Palm Reading | B | interface | Feature-zone → meaning rule tables (image features extracted by a multimodal model) |
| `tarot` | Tarot | C | complete | 78 cards, upright/reversed, four spreads, seed-reproducible draws |
| `oracle` | Oracle Sticks & Dream Interpretation | C | sample | Sample stick library / keyword lookup (swap in a full corpus or vector RAG for production) |

**Maturity**: `complete` fully recomputable by pure rules with unit tests ｜ `core` core casting works, deep interpretation goes to the model ｜ `partial` deterministic front stage, back stage left as an interface ｜ `rules` rule layer complete, raw input needs an external library ｜ `interface` rule tables complete, features come from a multimodal model ｜ `sample` retrieval over sample data, swap in real corpus for production.

## 3. CLI

```
dayan list                     # List all engines and their inputs
dayan cast <engine> key=value  # Unified casting entry (--json for structured output)
dayan selftest                 # Deterministic smoke test of all 16 engines
dayan generate                 # Batch-generate SFT JSONL (--domains/--per-domain/--tool-ratio/--processes)
dayan probe                    # Holdout canary: model answers vs engine ground truth (--backend echo/openai/mlx)
dayan report                   # Aggregate request logs into a daily report (--markdown)
```

<details>
<summary>More cast examples</summary>

```bash
dayan cast qimen dun=阳 ju=1 hour_ganzhi=甲子
dayan cast meihua mode=number n1=5 n2=8 --json
dayan cast xuankong year=2024 mountain=子 facing=午
dayan cast ziwei year=1995 month=8 day=2 hour=6 gender=female
```

</details>

## 4. Project Layout

```
src/dayan/
├── core/                 # Cross-engine shared layer (pure rules, zero external deps, auditable)
│   ├── wuxing.py         #   Yin-yang & five elements, heavenly stems & earthly branches, NaYin,
│   │                     #   ten gods, clashes/combos/harms, symbolic stars, stem-branch escaping
│   ├── gua.py            #   Trigrams / 64 hexagrams / Jing Fang palaces / na jia / transformations
│   ├── lunar_cal.py      #   lunar-python wrapper (Li Chun year switch, solar-term months, true solar time)
│   ├── paths.py          #   Single hardened entry point for all file output
│   └── registry.py       #   Engine registry, input coercion, unified cast dispatch
├── engines/              # 16 engines, one file each — @register to plug in
├── sft/                  # prompts.py per-art system prompts; generator.py SFT data factory
├── observe/              # facts extraction / canary probes / metrics reports / monitored gateway
└── cli.py                # list / cast / selftest / generate / probe / report
scripts/                  # Unsloth QLoRA (NVIDIA), MLX conversion & one-shot training (Apple), gateway
configs/                  # LLaMA-Factory / MLX configs
assets/eval_rubric.md     # Interpretation-quality rubric (human / LLM judge)
tests/                    # 39 unit tests (core rules + all engines + data + monitoring)
```

**Add a new engine in 5 minutes**:

1. Create `engines/myart.py`, decorate `cast_myart(**kw)` with `@register("myart", "name", tier, maturity, inputs=[...])`; return a dict containing a `text` field.
2. Add the import to `engines/__init__.py`.
3. Add a random-input sampler `_s_myart` and two phrasings in `ASK["myart"]` in `sft/generator.py`.
4. Add a unit test. CLI / SFT / registry wiring happens automatically.

## 5. SFT Data Format

ShareGPT/OpenAI-style messages; about 40% are **tool-call samples** that teach the model to call the unified tool `dayan_cast(engine, params)` first, then interpret the engine result:

```
system(per-art prompt) → user → assistant(tool_calls) → tool(engine result) → assistant(interpretation + disclaimer)
```

Every deterministic part of every assistant answer is computed live by the engines — never hand-written, never fabricated.

## 6. Training Routes

<details open>
<summary><b>NVIDIA: Qwen3.8-27B (Unsloth QLoRA)</b></summary>

```bash
pip install unsloth trl transformers datasets torch
dayan generate --per-domain 200                 # scale up the data first
python scripts/train_unsloth_qwen38.py --merge  # or use the LLaMA-Factory configs/
```

- QLoRA 4bit needs roughly 18–24GB VRAM; LoRA must cover the hybrid attention (Gated DeltaNet) projections — the script prints and includes all `*_proj` modules automatically.
- Freeze the vision tower for text-only tasks; set `reasoning_effort` to medium/low at inference.

</details>

<details>
<summary><b>Apple Silicon (M4/M-series, 24GB): Qwen3-8B (MLX)</b></summary>

Unsloth / bitsandbytes are CUDA-only — **on Mac use Apple's native `mlx-lm`**; the rule engines and SFT data are base-model agnostic and reused as-is.

```bash
pip install -e ".[mac]"                              # macOS / Apple Silicon only
dayan generate --per-domain 200 --tool-ratio 0.2     # 8B keeps some tool samples; use 0 for 4B and below
MODEL=mlx-community/Qwen3-8B-4bit bash scripts/train_mlx_qwen.sh
```

Step-by-step equivalent:

```bash
python scripts/convert_to_mlx.py
python -m mlx_lm.lora --config configs/mlx_qwen3_8b_lora.yaml
python -m mlx_lm.fuse --model mlx-community/Qwen3-8B-4bit \
        --adapter-path adapters/qwen3-8b-dayan --save-path models/qwen3-8b-dayan
python -m mlx_lm.server --model models/qwen3-8b-dayan   # local OpenAI-compatible server
```

| Model | 4bit LoRA training footprint (est.) | Suggestion on 24GB M4 |
|---|---|---|
| Qwen3-4B | ~5–8GB | Smoke test / fast iteration |
| **Qwen3-8B** | ~8–12GB | **Main workhorse**: max_seq_length=2048, batch=1, grad_accumulate=8 |
| Qwen3-14B | ~13–17GB | Upper bound, slow |
| Qwen3.8-27B | Weights already near the memory ceiling | Not recommended on Mac |

Multimodal arts (face/palm reading) need a Qwen3-VL base; the other 13 text arts follow this flow.

</details>

## 7. Evaluation & Monitoring (the `observe` subpackage)

Four verification layers, most-automated first:

| Layer | How | Pass criteria |
|---|---|---|
| 1. Engine self-test | `dayan selftest` | All 16 engines pass — the "calculator" itself is correct |
| 2. During training | train/eval loss | Early-stop when eval loss rises (overfitting) |
| 3. Post-training canary | `dayan probe` (holdout set, seed 999 ≠ training seed 42) | `fact_hit_rate` ≈ 100% for casting arts |
| 4. Interpretation quality | 5-dimension rubric in `assets/eval_rubric.md` (D1 chart fidelity … D5 expression) | D2–D5 average ≥ 4, zero red-line violations |

```bash
# Self-check the evaluator first, with no model (must be fact=1.0)
dayan probe --backend echo

# Once the model server is up (mlx_lm.server / Ollama / vLLM)
dayan probe --backend openai --base-url http://127.0.0.1:8080/v1 \
            --n-per-engine 20 --log evals/requests.jsonl --badcase evals/bad.jsonl
```

**Production monitoring gateway** (recommended architecture: the engine casts first, the model only interprets):

```bash
python scripts/serve_monitored.py --port 9000 --log evals/requests.jsonl
dayan report --log evals/requests.jsonl --markdown --out evals/daily.md
```

The gateway exposes `/chat` (engine casts → model interprets → fact cross-check → log), `/healthz`, and `/report`. It listens on `127.0.0.1` only by default; upstream model URLs must be http(s) and are restricted to loopback/private networks unless `--allow-public-url` is passed. Metrics: request volume per art, deterministic-fact hit rate, full-match rate, disclaimer coverage, boundary-violation flag rate, P50/P95 latency.

## 8. Scope & Caveats (please read)

- Calendar computation (solar terms, Ganzhi, luck pillars, almanac) relies on the mature pure-Python library `lunar-python==1.4.4`; all divination rules are self-implemented, unit-tested, and auditable.
- `ziwei` star placement uses commonly-circulated formulas; **leap-month handling differs across schools** — cross-check against professional charting software before production SFT.
- `qimen` ships the mainstream **Chai Bu** ju resolution (24-term ju table + day-pillar fu-tou for the three yuan); manual dun/ju is also accepted. Zhi Run / Mao Shan schools are not built in; center-palace lodging in Kun palace 2 is handled. Calendar correctness is guarded by JDN golden-anchor tests (`tests/test_engine_accuracy.py`).
- `liuren` covers only up to the four lessons — the three transmissions (nine schools) have many branches; `astrology` ships no ephemeris — install `pyswisseph` and supply positions yourself.
- `physiognomy` does no pixel recognition; image → structured features is delegated to a multimodal model, the engine only maps "zone → meaning".
- All output is positioned as **traditional metaphysics cultural reference and entertainment**, with a unified disclaimer. No assertions about disaster, lifespan, or death; not medical, investment, or legal advice.

## License

[MIT](LICENSE)
