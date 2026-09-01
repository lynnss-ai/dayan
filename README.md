<div align="center">

# 大衍 dayan

**多术数确定性规则引擎 + 玄学 SFT 数据工厂**

*「大衍之数五十，其用四十有九」——《周易·系辞》*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](pyproject.toml)
[![Tests](https://img.shields.io/badge/tests-39%20passed-brightgreen.svg)](tests)
[![Engines](https://img.shields.io/badge/%E6%9C%AF%E6%95%B0%E5%BC%95%E6%93%8E-16-9B59B6.svg)](#二引擎总览)

**简体中文** | [English](README.en.md)

</div>

---

## 这是什么

面向 **Qwen3.8-27B / Qwen3** 私有化微调的玄学领域工程。核心理念一句话：

> **确定性的「排盘/起卦/排布」全部交给可审计的规则引擎，模型只学表达与解读。**
> 同一个输入必得同一个盘，从根上杜绝模型在干支、卦爻、星曜上"算错"。

三句话概括：

- **16 个术数引擎**：八字、紫微、奇门、六爻、塔罗……统一注册、统一 CLI、统一 SFT 产出，纯 Python 可复算、可单测、可审计；
- **数据工厂**：确定性答案全部由引擎现算（含 40% 工具调用样本），不手写、不杜撰；
- **验证闭环**：自带留出集对拍探针、线上监控网关与指标日报，`fact_hit_rate` 直接量化模型有没有"算错"。

## 快速开始

```bash
# 安装
pip install -e ".[dev]"

# 排一个八字
dayan cast bazi year=1990 month=3 day=15 hour=12 gender=male

# 16 引擎确定性冒烟 + 单测
dayan selftest && pytest -q

# 批量生成多术数 SFT 数据（默认 40% 工具调用样本）
dayan generate --per-domain 40 --outdir data
```

作为库调用：

```python
import dayan
chart = dayan.cast("bazi", year=1990, month=3, day=15, hour=12, gender="male")
print(chart["text"])
```

## 二、引擎总览

| key | 术数 | 等级 | 成熟度 | 确定性产出 |
|---|---|---|---|---|
| `bazi` | 八字四柱 | A | complete | 四柱、藏干十神、纳音、五行旺衰、刑冲合害/神煞/旬空、大运、流年 |
| `almanac` | 择日黄历 | S | complete | 建除、值神黄黑道、二十八宿、宜忌、冲煞、彭祖百忌、十二时辰 |
| `name` | 姓名五格 | S | complete | 天人地外总五格、81 数理、三才五行（需康熙笔画） |
| `meihua` | 梅花易数 | S | complete | 时间/数字起卦、本互变、体用生克、卦气 |
| `numerology` | 生命灵数 | S | complete | 生命路径数、天赋数、大师数 |
| `bazhai` | 八宅风水 | S | complete | 命卦、东西四命、大游年八方吉凶 |
| `zhouyi` | 周易卦爻 | S | complete | 卦宫、世应、错/综/互/变卦 |
| `xuankong` | 玄空飞星 | A | complete | 三元九运、运盘/山盘/向盘洛书飞布 |
| `liuyao` | 六爻纳甲 | A | core | 装卦、纳甲、世应、六亲六神、变卦（断卦交模型） |
| `ziwei` | 紫微斗数 | A | core | 命身宫、五行局、安十四正曜、生年四化、大限 |
| `qimen` | 奇门遁甲 | A | core | 给定遁/局/时柱排天地盘、九星八门八神、值符值使 |
| `liuren` | 大六壬 | A | partial | 月将加时天地盘、四课（三传九宗门留接口） |
| `astrology` | 西方占星 | A | rules | 元素模式、相位 orb、宫主星飞星（行星位置需 pyswisseph/上游） |
| `physiognomy` | 面相手相峦头 | B | interface | 部位/线丘/形煞→含义规则表（图像特征由多模态抽取） |
| `tarot` | 塔罗 | C | complete | 78 张牌、正逆位、四种牌阵、种子可复现抽牌 |
| `oracle` | 灵签解梦 | C | sample | 样例签库/关键词检索（生产换完整语料或向量 RAG） |

**成熟度含义**：`complete` 纯规则可完整复算且有单测 ｜ `core` 核心排布可算、深层断法交模型 ｜ `partial` 确定性前段、后段留接口 ｜ `rules` 规则层完整、原始输入需外部库 ｜ `interface` 规则表完整、特征靠多模态 ｜ `sample` 检索样例、生产需换语料。

## 三、CLI 一览

```
dayan list                     # 查看全部引擎与入参
dayan cast <引擎> key=value    # 统一排盘入口（--json 出结构化）
dayan selftest                 # 16 引擎确定性冒烟
dayan generate                 # 批量生成 SFT JSONL（--domains/--per-domain/--tool-ratio）
dayan probe                    # 留出集对拍：模型答案 vs 引擎真值（--backend echo/openai/mlx）
dayan report                   # 聚合请求日志出监控日报（--markdown）
```

<details>
<summary>更多 cast 示例</summary>

```bash
dayan cast qimen dun=阳 ju=1 hour_ganzhi=甲子
dayan cast meihua mode=number n1=5 n2=8 --json
dayan cast xuankong year=2024 mountain=子 facing=午
dayan cast ziwei year=1995 month=8 day=2 hour=6 gender=female
```

</details>

## 四、工程结构

```
src/dayan/
├── core/                 # 跨术数共享层（纯规则、零外部依赖，便于审计）
│   ├── wuxing.py         #   阴阳五行、天干地支、纳音、十神、刑冲合害、神煞、五虎/五鼠遁
│   ├── gua.py            #   八卦/64卦/京房八宫/纳甲纳支/错综互变
│   ├── lunar_cal.py      #   lunar-python 历法封装（立春换年、节气换月、真太阳时）
│   ├── paths.py          #   输出文件统一安全写入入口
│   └── registry.py       #   引擎注册表、入参类型转换、统一 cast 调度
├── engines/              # 16 个术数引擎，每个文件一个，@register 即接入
├── sft/                  # prompts.py 分术数系统提示；generator.py 多术数 SFT 工厂
├── observe/              # facts 事实抽取 / canary 对拍探针 / metrics 指标日报 / gateway 监控网关
└── cli.py                # list / cast / selftest / generate / probe / report
scripts/                  # Unsloth QLoRA（NVIDIA）、MLX 转换与一键训练（Apple）、监控网关
configs/                  # LLaMA-Factory / MLX 配置
assets/eval_rubric.md     # 解读层人工/裁判评分表
tests/                    # 39 个单测（核心规则 + 全部引擎 + 数据结构 + 监控）
```

**新增一个术数引擎（5 分钟）**：

1. 在 `engines/` 新建 `myart.py`，用 `@register("myart", "中文名", tier, maturity, inputs=[...])` 装饰 `cast_myart(**kw)`，返回 dict 带一个 `text` 字段；
2. 在 `engines/__init__.py` 追加 import；
3. 在 `sft/generator.py` 加一个随机入参采样器 `_s_myart` 和两条自然问法 `ASK["myart"]`；
4. 补一个单测。其余 CLI / SFT / 注册全自动生效。

## 五、SFT 数据格式

ShareGPT/OpenAI 风格 messages；约 40% 为**工具调用样本**，教模型先调统一工具 `dayan_cast(engine, params)`、拿到引擎结果再解读：

```
system(分术数提示) → user → assistant(tool_calls) → tool(引擎结果) → assistant(解读+免责)
```

所有 assistant 的确定性部分都由引擎现算，不手写、不杜撰。

## 六、训练路线

<details open>
<summary><b>NVIDIA：Qwen3.8-27B（Unsloth QLoRA）</b></summary>

```bash
pip install unsloth trl transformers datasets torch
dayan generate --per-domain 200                 # 先放大数据量
python scripts/train_unsloth_qwen38.py --merge  # 或用 configs/ 的 LLaMA-Factory
```

- QLoRA 4bit 约 18–24GB 显存；LoRA 需覆盖混合注意力（Gated DeltaNet）投影，脚本会自动打印并纳入 `*_proj`；
- 纯文本任务冻结视觉塔；线上把 `reasoning_effort` 调到 medium/low。

</details>

<details>
<summary><b>Apple Silicon（M4/M 系列 24GB）：Qwen3-8B（MLX）</b></summary>

Unsloth / bitsandbytes 是 CUDA 专用，**在 Mac 上改用苹果原生 `mlx-lm`**；规则引擎与 SFT 数据与基座无关、原样复用。

```bash
pip install -e ".[mac]"                              # 仅 macOS / Apple Silicon
dayan generate --per-domain 200 --tool-ratio 0.2     # 8B 保留少量工具样本；4B 以下用 0
MODEL=mlx-community/Qwen3-8B-4bit bash scripts/train_mlx_qwen.sh
```

分步等价：

```bash
python scripts/convert_to_mlx.py
python -m mlx_lm.lora --config configs/mlx_qwen3_8b_lora.yaml
python -m mlx_lm.fuse --model mlx-community/Qwen3-8B-4bit \
        --adapter-path adapters/qwen3-8b-dayan --save-path models/qwen3-8b-dayan
python -m mlx_lm.server --model models/qwen3-8b-dayan   # 本地 OpenAI 兼容服务
```

| 模型 | 4bit LoRA 训练占用（估算） | 24GB M4 建议 |
|---|---|---|
| Qwen3-4B | 约 5–8GB | 跑通流程/快速迭代 |
| **Qwen3-8B** | 约 8–12GB | **主力**：max_seq_length=2048、batch=1、grad_accumulate=8 |
| Qwen3-14B | 约 13–17GB | 上限，偏慢 |
| Qwen3.8-27B | 权重已贴近内存上限 | 不建议在 Mac 训练 |

面相/手相等多模态术数需 Qwen3-VL 底座，其余 13 个文本术数走本流程即可。

</details>

## 七、验证与监控（observe 子包）

四层验证，越靠前越自动化：

| 层 | 手段 | 通过标准 |
|---|---|---|
| 1. 引擎自检 | `dayan selftest` | 16 引擎全过，"计算器"本身正确 |
| 2. 训练中 | train/eval loss | eval loss 回升即过拟合，早停 |
| 3. 训练后对拍 | `dayan probe`（seed 999 留出集，与训练 seed 42 错开） | `fact_hit_rate`≈100%（排盘类） |
| 4. 解读质量 | `assets/eval_rubric.md` 五维评分（D1 排盘一致…D5 表达） | D2–D5 均分 ≥4、红线 0 容忍 |

```bash
# 无模型时先自检评估器（必须 fact=1.0）
dayan probe --backend echo

# 模型服务起来后（mlx_lm.server / Ollama / vLLM）
dayan probe --backend openai --base-url http://127.0.0.1:8080/v1 \
            --n-per-engine 20 --log evals/requests.jsonl --badcase evals/bad.jsonl
```

**线上监控网关**（推荐生产架构：引擎先算、模型只解读）：

```bash
python scripts/serve_monitored.py --port 9000 --log evals/requests.jsonl
dayan report --log evals/requests.jsonl --markdown --out evals/daily.md
```

网关暴露 `/chat`（引擎算盘→模型解读→事实对拍→记录）、`/healthz`、`/report`。默认只监听本机 `127.0.0.1`，上游模型地址限 http(s) 且默认仅本机/内网（公网需 `--allow-public-url`）。监控指标：请求量/分术数、确定性事实命中率、全对率、免责声明覆盖率、越界标记率、延迟 P50/P95。

## 八、口径与边界（务必阅读）

- 历法（节气、干支、大运、黄历）依赖成熟纯 Python 库 `lunar-python==1.4.4`；玄学规则全部自研、可单测、可审计。
- `ziwei` 安星采用通行口诀，**闰月处理与个别流派存在差异**，生产 SFT 前请与专业排盘软件抽样核对。
- `qimen` 只负责"已确定遁/局后的排布"，节气定局（拆补/置闰/茅山）由上层传入；中宫寄坤二宫已处理。
- `liuren` 三传九宗门分支繁多，本版只到四课；`astrology` 不内置星历，装 `pyswisseph` 后自行补位置。
- `physiognomy` 不做像素识别，图像→结构化特征交给多模态模型，引擎只做"部位→含义"。
- 全部输出定位为**传统命理/玄学文化参考与娱乐**，统一附免责声明，不做灾祸、寿命、生死断言，不构成医疗/投资/法律建议。

## License

[MIT](LICENSE)
