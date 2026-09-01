# 玄枢 xuanshu · 多术数确定性规则引擎 + 玄学 SFT 数据工厂

> 「玄」承玄学，「枢」为枢机枢纽——统一的多术数排盘引擎中枢与私有化微调数据工厂。

面向 **Qwen3.8-27B / Qwen3** 私有化微调的玄学领域工程。核心理念：

> **确定性的「排盘/起卦/排布」全部交给可审计的规则引擎，模型只学表达与解读。**
> 同一个输入必得同一个盘，从根上杜绝模型在干支、卦爻、星曜上"算错"。

本项目由八字单引擎升级而来，现包含 **16 个术数引擎**，统一注册、统一 CLI、统一 SFT 产出。

---

## 一、引擎清单与成熟度

| key | 术数 | 等级 | 成熟度 | 确定性产出 |
|---|---|---|---|---|
| `bazi` | 八字四柱 | A | complete | 四柱、藏干十神、纳音、五行旺衰、**刑冲合害/神煞/旬空**、大运、流年 |
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
| `liuren` | 大六壬 | A | partial | 月将加时天地盘、四课（**三传九宗门留接口**） |
| `astrology` | 西方占星 | A | rules | 元素模式、相位 orb、宫主星飞星（**行星位置需 pyswisseph/上游**） |
| `physiognomy` | 面相手相峦头 | B | interface | 部位/线丘/形煞→含义规则表（**图像特征由多模态抽取**） |
| `tarot` | 塔罗 | C | complete | 78 张牌、正逆位、四种牌阵、种子可复现抽牌 |
| `oracle` | 灵签解梦 | C | sample | 样例签库/关键词检索（**生产换完整语料或向量 RAG**） |

**成熟度含义**：complete=纯规则可完整复算且有单测；core=核心排布可算、深层断法交模型；
partial=确定性前段、后段留接口；rules=规则层完整、原始输入需外部库；
interface=规则表完整、特征靠多模态；sample=检索样例、生产需换语料。

---

## 二、安装与命令行

```bash
pip install -e ".[dev]"
xuanshu list                     # 查看全部引擎与入参
xuanshu selftest                 # 16 引擎确定性冒烟
pytest -q                        # 39 个单测

# 统一调用：xuanshu cast <引擎> key=value ...
xuanshu cast bazi year=1990 month=3 day=15 hour=12 gender=male
xuanshu cast qimen dun=阳 ju=1 hour_ganzhi=甲子
xuanshu cast meihua mode=number n1=5 n2=8 --json
xuanshu cast xuankong year=2024 mountain=子 facing=午

# 批量生成多术数 SFT（默认 16 引擎 × 30 条，含 40% 工具调用样本）
xuanshu generate --per-domain 30 --outdir data
```

也可作为库使用：
```python
import xuanshu
chart = xuanshu.cast("bazi", year=1990, month=3, day=15, hour=12, gender="male")
print(chart["text"])
```

---

## 三、工程结构

```
src/xuanshu/
├── core/                 # 跨术数共享层（纯规则、零外部依赖，便于审计）
│   ├── wuxing.py         # 阴阳五行、天干地支、六十甲子纳音、十神、刑冲合害、神煞、五虎/五鼠遁
│   ├── gua.py            # 八卦/64卦/京房八宫/纳甲纳支/错综互变
│   ├── lunar_cal.py      # lunar-python 历法封装（立春换年、节气换月、真太阳时）
│   └── registry.py       # 引擎注册表、入参类型转换、统一 cast 调度
├── engines/              # 16 个术数引擎，每个文件一个，@register 即接入
│   ├── bazi.py / almanac.py / name_fivegrid.py / meihua.py / numerology.py
│   ├── bazhai.py / zhouyi.py / xuankong.py / liuyao.py / ziwei.py
│   ├── qimen.py / liuren.py / astrology.py / physiognomy.py / tarot.py / oracle.py
├── sft/                  # prompts.py 分术数系统提示；generator.py 多术数 SFT 工厂
├── observe/              # 验证与监控：facts 事实抽取、canary 对拍探针、metrics 指标日报、gateway 监控网关
└── cli.py                # list / cast / selftest / generate / probe / report
scripts/train_unsloth_qwen38.py   # Unsloth QLoRA（NVIDIA）
scripts/convert_to_mlx.py         # SFT -> mlx-lm 格式（Apple）
scripts/train_mlx_qwen.sh         # MLX 一键训练 Qwen3-8B（Apple M 系列）
scripts/serve_monitored.py        # 引擎先算→模型解读 的监控网关
configs/                          # LLaMA-Factory / MLX 配置
assets/eval_rubric.md             # 解读层人工/裁判评分表
tests/                            # 39 个单测（核心规则 + 全部引擎 + 数据结构 + 监控）
```

### 新增一个术数引擎（5 分钟）
1. 在 `engines/` 新建 `myart.py`，用 `@register("myart", "中文名", tier, maturity, inputs=[...])` 装饰 `cast_myart(**kw)`，返回的 dict 里带一个 `text` 字段；
2. 在 `engines/__init__.py` 追加 import；
3. 在 `sft/generator.py` 加一个随机入参采样器 `_s_myart` 和两条自然问法 `ASK["myart"]`；
4. 补一个单测。其余 CLI / SFT / 注册全自动生效。

---

## 四、数据格式

ShareGPT/OpenAI 风格 messages；约 40% 为**工具调用样本**，教模型先调统一工具
`xuanshu_cast(engine, params)`、拿到引擎结果再解读：
```
system(分术数提示) → user → assistant(tool_calls) → tool(引擎结果) → assistant(解读+免责)
```
所有 assistant 的确定性部分都由引擎现算，不手写、不杜撰。

---

## 五、训练（NVIDIA 路线：Qwen3.8-27B）
```bash
pip install unsloth trl transformers datasets torch
xuanshu generate --per-domain 200                 # 先放大数据量
python scripts/train_unsloth_qwen38.py --merge     # 或用 configs/ 的 LLaMA-Factory
```
要点：QLoRA 4bit 约 18–24GB 显存；LoRA 需覆盖混合注意力（Gated DeltaNet）投影，
脚本会自动打印并纳入 `*_proj`；纯文本任务冻结视觉塔；线上把 `reasoning_effort` 调到 medium/low。

---

## 五·补、Apple Silicon（M4/M 系列，24GB 统一内存）路线：Qwen3-8B

> Unsloth / bitsandbytes 是 CUDA 专用，**在 Mac 上改用苹果原生 `mlx-lm`**。
> 规则引擎与 SFT 数据与基座无关、原样复用；24GB 的甜点模型是 **Qwen3-8B（4bit LoRA）**，
> 调试可先换 `mlx-community/Qwen3-4B-4bit`。Qwen3-8B 为标准注意力，LoRA 比 27B 混合架构更简单。

```bash
pip install -e ".[mac]"                              # 仅 macOS/Apple Silicon
xuanshu generate --per-domain 200 --tool-ratio 0.2   # 8B 保留少量工具样本；4B 以下用 0
MODEL=mlx-community/Qwen3-8B-4bit bash scripts/train_mlx_qwen.sh   # 转数据→训练→合并→试生成
```

分步等价命令：
```bash
python scripts/convert_to_mlx.py
python -m mlx_lm.lora --config configs/mlx_qwen3_8b_lora.yaml
python -m mlx_lm.fuse --model mlx-community/Qwen3-8B-4bit \
        --adapter-path adapters/qwen3-8b-xuanshu --save-path models/qwen3-8b-xuanshu
python -m mlx_lm.server --model models/qwen3-8b-xuanshu   # 本地 OpenAI 兼容服务
```

| 模型 | 4bit LoRA 训练占用（估算） | 24GB M4 建议 |
|---|---|---|
| Qwen3-4B | 约 5–8GB | 跑通流程/快速迭代 |
| **Qwen3-8B** | 约 8–12GB | **主力**：max_seq_length=2048、batch=1、grad_accumulate=8 |
| Qwen3-14B | 约 13–17GB | 上限，偏慢 |
| Qwen3.8-27B | 权重已贴近内存上限 | 不建议在 Mac 训练 |

- 两台同配 Mac **不能合并内存训一个更大模型**；建议 A 机训练，B 机并行造数/跑 pytest/加载合并模型捞 badcase。
- 转换脚本把工具调用拍平成「问→调用工具→【工具返回】→解读」纯文本链，只留 system/user/assistant，小模型更稳。
- 若 `mlx_lm.lora` 报参数不存在，以 `python -m mlx_lm.lora --help` 为准（旧版 `max_seq_length` 叫 `seq_length`、可能无 `grad_accumulate`，删键即可）。
- 面相/手相等多模态术数需 Qwen3-VL 底座，其余 13 个文本术数走本流程即可。

---

## 五·再补、训练后验证与线上监控（observe 子包）

分四层，越靠前越自动化：

1. **引擎自检**：`xuanshu selftest`，保证"计算器"本身正确。
2. **训练中**：看 train/eval loss，eval loss 回升即过拟合、早停。
3. **训练后对拍（自动）**：用训练没见过的留出样本（seed 999）问模型，再和引擎真值比对关键事实。
   ```bash
   # 无模型时先自检评估器（必须 fact=1.0）
   xuanshu probe --backend echo
   # 模型服务起来后（mlx_lm.server / Ollama / vLLM）
   xuanshu probe --backend openai --base-url http://127.0.0.1:8080/v1 \
                 --n-per-engine 20 --log evals/requests.jsonl --badcase evals/bad.jsonl
   ```
   输出 `fact_hit_rate`（关键事实命中率，排盘类要求≈100%）、`full_match_rate`、免责覆盖率、P95 延迟、分术数明细；错例落 badcase 回流。
4. **解读质量（人工/裁判）**：按 `assets/eval_rubric.md` 五维打分（D1 排盘一致…D5 表达），红线 0 容忍；另抽通用中文任务防能力退化。

**线上监控网关（推荐生产架构：引擎先算、模型只解读）**：
```bash
# 先起模型服务，再起网关；每次请求自动对拍+留痕
python scripts/serve_monitored.py --port 9000 --log evals/requests.jsonl
xuanshu report --log evals/requests.jsonl --markdown --out evals/daily.md   # 出日报
```
网关暴露 `/chat`（引擎算盘→模型解读→事实对拍→记录）、`/healthz`、`/report`。
监控指标：请求量/分术数、确定性事实命中率、全对率、免责声明覆盖率、越界标记率、延迟 P50/P95。
两台 Mac 可一台跑模型+网关、一台定时 `probe` 巡检并出日报。

---

## 六、口径与边界（务必阅读）

- 历法（节气、干支、大运、黄历）依赖成熟纯 Python 库 `lunar-python==1.4.4`；玄学规则全部自研、可单测、可审计。
- `ziwei` 安星采用通行口诀，**闰月处理与个别流派存在差异**，生产 SFT 前请与专业排盘软件抽样核对。
- `qimen` 只负责"已确定遁/局后的排布"，**节气定局（拆补/置闰/茅山）由上层传入**；中宫寄坤二宫已处理。
- `liuren` 三传九宗门分支繁多，本版只到四课；`astrology` 不内置星历，装 `pyswisseph` 后自行补位置。
- `physiognomy` 不做像素识别，图像→结构化特征交给 Qwen3.8 多模态，引擎只做"部位→含义"。
- 全部输出定位为**传统命理/玄学文化参考与娱乐**，统一附免责声明，不做灾祸、寿命、生死断言，不构成医疗/投资/法律建议。
