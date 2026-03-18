import argparse
import json

from runtime_service import worker_loop
from sql_database import initialize_db


def _emit_json(payload):
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _ok(data):
    return {"ok": True, "data": data}


def _err(message):
    return {"ok": False, "error": message}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Internal runtime entrypoint")
    parser.add_argument("--mode", choices=["worker", "health"], default="worker")
    parser.add_argument("--poll-interval", type=float, default=1.0)
    args = parser.parse_args()

    if args.mode == "worker":
        worker_loop(poll_interval=args.poll_interval)
    elif args.mode == "health":
        try:
            initialize_db()
            _emit_json(_ok({"status": "up"}))
        except Exception as e:
            _emit_json(_err(str(e)))
            raise SystemExit(1)
