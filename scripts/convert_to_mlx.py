# -*- coding: utf-8 -*-
"""
convert_to_mlx.py —— 把本项目 messages JSONL 转成 mlx-lm 微调所需格式。
mlx-lm（Apple Silicon 原生）LoRA 训练读取目录下的 train.jsonl / valid.jsonl，
每行支持 {"messages": [{"role":..., "content":...}, ...]} 的 chat 形式，
训练时用底座 tokenizer 自带的 chat template 渲染。为最大兼容性，本脚本：
  1) 只保留 system / user / assistant 三种角色；
  2) assistant 的 tool_calls 拍平成一句“调用工具：...”文本；
  3) role=tool 的引擎返回改写成 user 角色的“【工具返回】...”，
     形成 问→调工具→返回→解读 的连贯文本链（小模型更易学、不依赖 tool 模板）。
用法：
    python scripts/convert_to_mlx.py \
        --train data/sft_train.jsonl --val data/sft_val.jsonl \
        --out data/mlx
输出：data/mlx/train.jsonl、data/mlx/valid.jsonl
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from dayan.core.paths import safe_write  # noqa: E402


def normalize(messages):
    out = []
    for m in messages:
        role, content = m.get("role"), m.get("content")
        if role == "assistant" and content is None and m.get("tool_calls"):
            calls = [tc["function"] for tc in m["tool_calls"]]
            content = "调用工具：" + json.dumps(calls, ensure_ascii=False)
            role = "assistant"
        if role == "tool":
            role, content = "user", "【工具返回】" + str(content)
        if role not in ("system", "user", "assistant"):
            continue
        out.append({"role": role, "content": content or ""})
    return out


def convert_file(src, dst):
    n = 0
    with open(src, "r", encoding="utf-8") as f, \
            safe_write(dst) as w:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            msgs = normalize(row["messages"])
            w.write(json.dumps({"messages": msgs}, ensure_ascii=False) + "\n")
            n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", default="data/sft_train.jsonl")
    ap.add_argument("--val", default="data/sft_val.jsonl")
    ap.add_argument("--out", default="data/mlx")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    n_tr = convert_file(args.train, os.path.join(args.out, "train.jsonl"))
    n_va = convert_file(args.val, os.path.join(args.out, "valid.jsonl"))
    print(f"[MLX] train={n_tr} -> {args.out}/train.jsonl")
    print(f"[MLX] valid={n_va} -> {args.out}/valid.jsonl")
    print("[MLX] 训练命令：bash scripts/train_mlx_qwen.sh")


if __name__ == "__main__":
    main()
