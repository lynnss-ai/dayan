#!/usr/bin/env bash
# Apple Silicon（M4 24GB）一键：转数据 -> MLX LoRA 训练 Qwen3-8B -> 合并 -> 试生成
# 依赖：pip install ".[mac]"  （即 mlx-lm；仅 macOS / Apple Silicon）
set -euo pipefail
cd "$(dirname "$0")/.."

MODEL="${MODEL:-mlx-community/Qwen3-8B-4bit}"
CFG="${CFG:-configs/mlx_qwen3_8b_lora.yaml}"
ADAPTER="adapters/qwen3-8b-dayan"
MERGED="models/qwen3-8b-dayan"

echo "[1/4] 转换 SFT 数据为 mlx-lm chat 格式 ..."
python3 scripts/convert_to_mlx.py

echo "[2/4] MLX 4bit LoRA 训练（活动监视器可看内存/Metal 占用）..."
python3 -m mlx_lm.lora --config "$CFG"

echo "[3/4] 把 LoRA 适配器合并回 4bit 底座（保持量化、省磁盘）..."
python3 -m mlx_lm.fuse \
  --model "$MODEL" \
  --adapter-path "$ADAPTER" \
  --save-path "$MERGED"

echo "[4/4] 试生成一条 ..."
python3 -m mlx_lm.generate \
  --model "$MERGED" \
  --prompt "帮我排八字：1990年3月15日12时出生，男"

echo "完成。合并模型在 $MERGED，可用 python -m mlx_lm.server --model $MERGED 起本地服务。"
