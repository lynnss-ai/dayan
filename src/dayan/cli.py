# -*- coding: utf-8 -*-
"""统一命令行：dayan {list,cast,selftest,generate,probe,report}。
示例：
  dayan list
  dayan cast bazi year=1990 month=3 day=15 hour=12 gender=male
  dayan cast qimen dun=阳 ju=1 hour_ganzhi=甲子 --json
  dayan generate --per-domain 40
"""
import argparse
import json
import multiprocessing
import os
import random
import sys

from .core.registry import REGISTRY, all_engines, get_engine
from .core.paths import resolve_out, safe_write
from .sft import generator as gen
from .observe import canary, metrics as M

TIER_ORDER = {"S": 0, "A": 1, "B": 2, "C": 3}


def _cmd_list(args) -> int:
    for e in sorted(all_engines(), key=lambda x: (TIER_ORDER[x.tier], x.key)):
        req = " ".join(f"{s.name}" + ("" if s.required else f"={s.default}")
                       for s in e.inputs)
        print(f"[{e.tier}/{e.maturity:9s}] {e.key:12s} {e.name_cn}\n"
              f"      入参: {req or '（无）'}\n      说明: {e.desc}")
    return 0


def _parse_kv(tokens):
    raw = {}
    for tok in tokens:
        if "=" not in tok:
            raise ValueError(f"参数需 key=value 形式：{tok}")
        k, v = tok.split("=", 1)
        raw[k.strip()] = v
    return raw


def _cmd_cast(args) -> int:
    spec = get_engine(args.engine)
    raw = _parse_kv(args.params)
    if args.strict:
        unknown = set(raw) - {s.name for s in spec.inputs}
        if unknown:
            raise ValueError(f"引擎 {args.engine} 不支持参数：{sorted(unknown)}，"
                             f"可用：{[s.name for s in spec.inputs]}（--strict 下报错）")
    kwargs = spec.coerce(raw)
    result = spec.cast(**kwargs)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["text"])
    return 0


def _cmd_selftest(args) -> int:
    rng = random.Random(0)
    ok = True
    for key in sorted(gen.SAMPLERS):
        try:
            kw = gen.SAMPLERS[key](rng)
            r = REGISTRY[key].cast(**kw)
            assert isinstance(r, dict) and r.get("text")
            print(f"[OK] {key:12s} {REGISTRY[key].name_cn}")
        except Exception as ex:  # noqa: BLE001
            ok = False
            print(f"[FAIL] {key}: {ex}")
    print("\n自检结果：", "全部通过 ✓" if ok else "存在失败 ✗")
    return 0 if ok else 1


def _spawn_safe() -> bool:
    """Windows 下多进程用 spawn，会重导入父进程 __main__。
    仅当入口是 `python -m dayan.cli`（文件自带 __main__ guard）时可安全多进程；
    控制台脚本入口（dayan.exe / dayan shell 脚本）在 Windows 上回退串行。"""
    if os.name != "nt":
        return True                            # POSIX 默认 fork，无重导入问题
    main_mod = sys.modules.get("__main__")
    f = getattr(main_mod, "__file__", "") or ""
    return os.path.basename(f) == "cli.py"


def _cmd_generate(args) -> int:
    domains = args.domains.split(",") if args.domains else None
    processes = args.processes
    if processes > 1 and not _spawn_safe():
        print(f"警告：当前入口不支持多进程（Windows 需 python -m dayan.cli），回退串行",
              file=sys.stderr)
        processes = 1
    n_tr, n_va, counts = gen.generate(
        domains=domains, per_domain=args.per_domain, seed=args.seed,
        val_ratio=args.val_ratio, outdir=args.outdir, tool_ratio=args.tool_ratio,
        processes=processes)
    print(f"共生成 train {n_tr} / val {n_va} 条，覆盖 "
          f"{len(set(k.split(':')[0] for k in counts))} 个引擎")
    print("分类计数：", json.dumps(counts, ensure_ascii=False))
    print(f"输出目录：{args.outdir}")
    return 0


def _cmd_probe(args) -> int:
    engines = args.engines.split(",") if args.engines else None
    probes = canary.build_probes(engines, args.n_per_engine, seed=args.seed)
    if args.backend == "echo":
        backend = canary.echo_backend
    elif args.backend == "blank":
        backend = canary.blank_backend
    elif args.backend == "mlx":
        backend = canary.mlx_backend(args.model)
    else:
        backend = canary.openai_backend(args.base_url, args.model,
                                        allow_public=args.allow_public_url)
    logger = None
    if args.log:
        args.log = resolve_out(args.log)
        logger = lambda rec: M.log(args.log, rec)  # noqa: E731
    summary, bad = canary.run_probes(backend, probes, logger, workers=args.workers)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.badcase:
        with safe_write(args.badcase) as f:
            for b in bad:
                f.write(json.dumps(b, ensure_ascii=False) + "\n")
        print(f"坏例 {len(bad)} 条 -> {args.badcase}", file=sys.stderr)
    if args.backend == "echo":
        rate = summary["fact_hit_rate"]
        return 0 if rate == 1.0 else 2
    return 0


def _cmd_report(args) -> int:
    agg = M.aggregate(M.load(args.log))
    text = M.render_markdown(agg) if args.markdown else json.dumps(agg, ensure_ascii=False, indent=2)
    if args.out:
        with safe_write(args.out) as f:
            f.write(text)
        print(f"报告已写入 {args.out}")
    else:
        print(text)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="dayan",
                                description="大衍 dayan：多术数确定性规则引擎 + 玄学 SFT 数据工厂")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="列出全部引擎与入参").set_defaults(func=_cmd_list)
    c = sub.add_parser("cast", help="调用某引擎，参数用 key=value")
    c.add_argument("engine")
    c.add_argument("params", nargs="*", help="key=value ...")
    c.add_argument("--json", action="store_true")
    c.add_argument("--strict", action="store_true",
                   help="未知入参直接报错（默认仅告警，防拼错参数静默走默认值）")
    c.set_defaults(func=_cmd_cast)
    sub.add_parser("selftest", help="对每个引擎做一次确定性冒烟").set_defaults(func=_cmd_selftest)
    g = sub.add_parser("generate", help="批量生成多术数 SFT JSONL")
    g.add_argument("--domains", default=None, help="逗号分隔的引擎名，默认全部")
    g.add_argument("--per-domain", type=int, default=40)
    g.add_argument("--seed", type=int, default=42)
    g.add_argument("--val-ratio", type=float, default=0.1)
    g.add_argument("--tool-ratio", type=float, default=0.4)
    g.add_argument("--processes", type=int, default=1,
                   help="并行进程数；>1 时每引擎独立子种子（结果与串行一致），Windows 需 python -m dayan.cli")
    g.add_argument("--outdir", default="data")
    g.set_defaults(func=_cmd_generate)
    pb = sub.add_parser("probe", help="对拍探针：模型答案 vs 规则引擎真值")
    pb.add_argument("--backend", choices=["echo", "blank", "mlx", "openai"], default="echo")
    pb.add_argument("--base-url", default="http://127.0.0.1:8080/v1")
    pb.add_argument("--allow-public-url", action="store_true",
                    help="允许公网模型服务地址（默认仅本机/内网，SSRF 防护）")
    pb.add_argument("--model", default="local")
    pb.add_argument("--engines", default=None, help="逗号分隔，默认全部 16 个")
    pb.add_argument("--n-per-engine", type=int, default=5)
    pb.add_argument("--seed", type=int, default=999)
    pb.add_argument("--log", default=None, help="逐条指标落此 JSONL")
    pb.add_argument("--badcase", default=None, help="错例输出 JSONL")
    pb.add_argument("--workers", type=int, default=1,
                    help="并发请求数；openai 后端建议 4-8（echo/blank/mlx 保持 1）")
    pb.set_defaults(func=_cmd_probe)
    rp = sub.add_parser("report", help="聚合请求日志出监控日报")
    rp.add_argument("--log", required=True)
    rp.add_argument("--out", default=None)
    rp.add_argument("--markdown", action="store_true")
    rp.set_defaults(func=_cmd_report)
    return p


def main(argv=None) -> int:
    # Windows spawn 子进程重导入入口脚本时会再次执行 main()，直接短路防止递归拉起
    if multiprocessing.current_process().name != "MainProcess":
        return 0
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
