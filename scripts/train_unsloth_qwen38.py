# -*- coding: utf-8 -*-
"""
train_unsloth_qwen38.py —— 用 Unsloth + QLoRA 在 Qwen3.8-27B 上做多术数玄学 SFT。
前置：NVIDIA GPU（24GB 起步，32-48GB 更从容），并安装训练依赖：
    pip install unsloth trl transformers datasets torch
数据：先用 `dayan generate --per-domain N` 生成 data/sft_train.jsonl、sft_val.jsonl
      （覆盖八字/择日/姓名/梅花/灵数/八宅/周易/玄空/六爻/紫微/奇门/六壬/占星/相法/塔罗/灵签）。
运行：
    python scripts/train_unsloth_qwen38.py \
        --model Qwen/Qwen3.8-27B --train data/sft_train.jsonl \
        --val data/sft_val.jsonl --out saves/qwen38-dayan --epochs 3
说明：
- Qwen3.8-27B 是「Gated DeltaNet 线性注意力 + Gated Attention」混合架构，
  脚本会打印模型里所有 *proj 模块名，请确认 LoRA 覆盖到线性注意力投影；
  若 Unsloth 版本尚不支持该层，请升级到最新版，或改用 configs/ 下的 LLaMA-Factory 方案。
- 纯文本任务建议冻结视觉塔（多模态部分）；手相/面相/风水实景等多模态样本另走 VLM SFT。
- 默认关闭冗长思考：数据已是「简短推导+结论」风格，线上 reasoning_effort 用 medium/low。
- 工具名统一为 dayan_cast(engine, params)，训练后模型学会"先调引擎再解读"。
"""
import argparse
import json


def load_jsonl(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def normalize_messages(messages):
    """把含 tool_calls / None 的消息规整为 chat_template 可渲染的纯文本消息。"""
    out = []
    for m in messages:
        role, content = m.get("role"), m.get("content")
        if role == "assistant" and content is None and m.get("tool_calls"):
            calls = [tc["function"] for tc in m["tool_calls"]]
            content = "调用工具：" + json.dumps(calls, ensure_ascii=False)
        if role == "tool" and content is not None:
            content = "工具返回：" + str(content)
        out.append({"role": role, "content": content or ""})
    return out


def discover_proj_modules(model):
    """打印并返回所有线性投影模块名，辅助确认 LoRA target。"""
    names = sorted({n.rsplit(".", 1)[-1]
                    for n, _ in model.named_modules() if n.endswith("_proj")})
    print("[INFO] 模型中的 *_proj 模块：", names)
    standard = {"q_proj", "k_proj", "v_proj", "o_proj",
                "gate_proj", "up_proj", "down_proj"}
    extra = [n for n in names if n not in standard]
    target = [n for n in names if n in standard] + extra
    print("[INFO] 本次 LoRA target_modules：", target)
    if extra:
        print("[INFO] 检测到额外投影（可能为线性注意力层），已一并纳入：", extra)
    return target


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen3.8-27B")
    ap.add_argument("--train", default="data/sft_train.jsonl")
    ap.add_argument("--val", default="data/sft_val.jsonl")
    ap.add_argument("--out", default="saves/qwen38-dayan")
    ap.add_argument("--epochs", type=float, default=3.0)
    ap.add_argument("--bs", type=int, default=1)
    ap.add_argument("--grad-accum", type=int, default=8)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--max-len", type=int, default=4096)
    ap.add_argument("--lora-r", type=int, default=16)
    ap.add_argument("--merge", action="store_true", help="训练后合并并导出 16bit 全量权重")
    args = ap.parse_args()

    import torch
    from datasets import Dataset
    from unsloth import FastLanguageModel
    from trl import SFTTrainer, SFTConfig

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.model, max_seq_length=args.max_len,
        dtype=None, load_in_4bit=True)
    target_modules = discover_proj_modules(model)
    model = FastLanguageModel.get_peft_model(
        model, r=args.lora_r, lora_alpha=args.lora_r * 2, lora_dropout=0.05,
        target_modules=target_modules, use_gradient_checkpointing="unsloth",
        random_state=42)

    def to_text(rows):
        texts = [tokenizer.apply_chat_template(
            normalize_messages(r["messages"]), tokenize=False,
            add_generation_prompt=False) for r in rows]
        return Dataset.from_dict({"text": texts})

    train_ds = to_text(load_jsonl(args.train))
    eval_ds = to_text(load_jsonl(args.val)) if args.val else None
    print(f"[INFO] train={len(train_ds)} eval={0 if eval_ds is None else len(eval_ds)}")

    trainer = SFTTrainer(
        model=model, tokenizer=tokenizer, train_dataset=train_ds,
        eval_dataset=eval_ds, dataset_text_field="text",
        max_seq_length=args.max_len,
        args=SFTConfig(
            output_dir=args.out, num_train_epochs=args.epochs,
            per_device_train_batch_size=args.bs,
            gradient_accumulation_steps=args.grad_accum,
            learning_rate=args.lr, lr_scheduler_type="cosine", warmup_ratio=0.05,
            bf16=torch.cuda.is_bf16_supported(), logging_steps=10, save_steps=200,
            eval_strategy="steps" if eval_ds else "no",
            eval_steps=200 if eval_ds else None,
            gradient_checkpointing=True, report_to="none"))
    trainer.train()
    model.save_pretrained(args.out + "/lora")
    tokenizer.save_pretrained(args.out + "/lora")
    if args.merge:
        model.save_pretrained_merged(args.out + "/merged", tokenizer,
                                     save_method="merged_16bit")
        print("[INFO] 已导出合并权重到", args.out + "/merged")


if __name__ == "__main__":
    main()
