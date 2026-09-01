# -*- coding: utf-8 -*-
"""
serve_monitored.py —— 「规则引擎先算 → 模型解读」的本地监控网关（生产推荐架构）。
模型不自己排盘：本服务先用 dayan 引擎算出确定结果，再把盘交给上游 OpenAI 兼容
模型（mlx_lm.server / Ollama / vLLM）做解读；每次请求记录延迟、确定性事实命中、
免责声明覆盖、异常到 JSONL，可用 `dayan report` 出日报。
启动（先在另一终端起模型服务，如 python -m mlx_lm.server --model models/... --port 8080）：
    MODEL_BASE_URL=http://127.0.0.1:8080/v1 MODEL_NAME=local \
        python scripts/serve_monitored.py --port 9000 --log evals/requests.jsonl
调用：
    curl -s localhost:9000/chat -H 'Content-Type: application/json' -d '{
      "engine":"bazi",
      "params":{"year":1990,"month":3,"day":15,"hour":12,"gender":"male"},
      "question":"帮我解读这个八字"}'
其他端点：GET /healthz、GET /report?fmt=markdown
"""
import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from dayan.observe import canary
from dayan.observe import metrics as M
from dayan.observe.gateway import handle_chat

LOG_PATH = "evals/requests.jsonl"


def make_handler(upstream, log_path):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, code, obj, ctype="application/json"):
            body = (json.dumps(obj, ensure_ascii=False, indent=2)
                    if ctype == "application/json" else str(obj)).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", ctype + "; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path.startswith("/healthz"):
                self._send(200, {"status": "ok"})
            elif self.path.startswith("/report"):
                agg = M.aggregate(M.load(log_path))
                if "fmt=markdown" in self.path:
                    self._send(200, M.render_markdown(agg), "text/markdown")
                else:
                    self._send(200, agg)
            else:
                self._send(404, {"error": "not found"})

        def do_POST(self):
            payload = {}
            if not self.path.startswith("/chat"):
                self._send(404, {"error": "not found"})
                return
            try:
                n = int(self.headers.get("Content-Length", 0))
                payload = json.loads(self.rfile.read(n).decode("utf-8"))
                out = handle_chat(payload, upstream, log_path)
                self._send(200, out)
            except Exception as e:  # noqa: BLE001
                M.log(log_path, {"engine": payload.get("engine", "?"),
                                 "ok": False, "flagged": True, "note": repr(e)})
                self._send(500, {"error": repr(e)})

        def log_message(self, *a):
            pass
    return Handler


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9000)
    ap.add_argument("--host", default="127.0.0.1",
                    help="监听地址，默认仅本机；确需局域网访问时再改为 0.0.0.0")
    ap.add_argument("--log", default=LOG_PATH)
    ap.add_argument("--base-url", default=os.environ.get("MODEL_BASE_URL", "http://127.0.0.1:8080/v1"))
    ap.add_argument("--model", default=os.environ.get("MODEL_NAME", "local"))
    ap.add_argument("--allow-public-url", action="store_true",
                    help="允许公网模型服务地址（默认仅本机/内网，SSRF 防护）")
    args = ap.parse_args()
    # 复用 canary 的 OpenAI 后端：单点实现 + 内置地址校验（http(s)、默认仅本机/内网）
    backend = canary.openai_backend(args.base_url, args.model,
                                    allow_public=args.allow_public_url)
    upstream = lambda s, u: backend(s, u, None)  # noqa: E731
    srv = ThreadingHTTPServer((args.host, args.port),
                              make_handler(upstream, args.log))
    print(f"大衍监控网关 {args.host}:{args.port}，上游 {args.base_url}，日志 {args.log}")
    srv.serve_forever()


if __name__ == "__main__":
    main()
