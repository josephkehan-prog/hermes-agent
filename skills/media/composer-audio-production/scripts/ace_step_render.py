#!/usr/bin/env python3
"""Manage the local ACE-Step API and render one reproducible audio take."""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


RUNTIME = Path("/Users/josephhan/mac/Hermes/runtimes/ace-step-1.5")
PYTHON = RUNTIME / ".venv/bin/python"
SERVER = RUNTIME / ".venv/bin/acestep-api"
CHECKPOINTS = RUNTIME / "checkpoints"
STATE = RUNTIME / ".hermes-runtime"
PID_FILE = STATE / "api.pid"
LOG_FILE = STATE / "api.log"
BASE_URL = "http://127.0.0.1:8001"
DEFAULT_OUTPUT = Path("/Users/josephhan/mac/GPTWorks/Hermes/media/audio")


def request_json(path: str, body: dict[str, object] | None = None, timeout: float = 30) -> dict[str, object]:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        BASE_URL + path,
        data=data,
        headers={"content-type": "application/json"} if data else {},
        method="POST" if data else "GET",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def healthy() -> bool:
    try:
        payload = request_json("/health", timeout=2)
        return payload.get("code") == 200
    except (OSError, urllib.error.URLError, ValueError):
        return False


def preflight() -> dict[str, object]:
    required = {
        "runtime": RUNTIME.is_dir(),
        "python": PYTHON.is_file(),
        "server": SERVER.is_file(),
        "dit": (CHECKPOINTS / "acestep-v15-turbo/model.safetensors").is_file(),
        "vae": (CHECKPOINTS / "vae/diffusion_pytorch_model.safetensors").is_file(),
        "text_encoder": (CHECKPOINTS / "Qwen3-Embedding-0.6B/model.safetensors").is_file(),
        "lm_0_6b": (CHECKPOINTS / "acestep-5Hz-lm-0.6B/model.safetensors").is_file(),
    }
    if required["python"]:
        probe = subprocess.run(
            [str(PYTHON), "-c", "import torch, mlx.core as mx; print(torch.backends.mps.is_available(), mx.metal.is_available())"],
            cwd=RUNTIME,
            text=True,
            capture_output=True,
            check=False,
        )
        required["mps_mlx"] = probe.returncode == 0 and probe.stdout.strip() == "True True"
    else:
        required["mps_mlx"] = False
    required["ready"] = all(bool(value) for value in required.values())
    required["running"] = healthy()
    return required


def start_server(timeout: float) -> bool:
    if healthy():
        return False
    STATE.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update({
        "ACESTEP_PROJECT_ROOT": str(RUNTIME),
        "ACESTEP_CHECKPOINTS_DIR": str(CHECKPOINTS),
        "ACESTEP_CONFIG_PATH": "acestep-v15-turbo",
        "ACESTEP_LM_MODEL_PATH": "acestep-5Hz-lm-0.6B",
        "ACESTEP_LM_BACKEND": "mlx",
        "ACESTEP_DOWNLOAD_SOURCE": "huggingface",
        "ACESTEP_NO_INIT": "false",
        "ACESTEP_BATCH_SIZE": "1",
        "TOKENIZERS_PARALLELISM": "false",
    })
    log = LOG_FILE.open("a", encoding="utf-8")
    process = subprocess.Popen(
        [str(SERVER), "--host", "127.0.0.1", "--port", "8001", "--download-source", "huggingface", "--lm-model-path", "acestep-5Hz-lm-0.6B"],
        cwd=RUNTIME,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    log.close()
    PID_FILE.write_text(f"{process.pid}\n", encoding="utf-8")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"ACE-Step server exited {process.returncode}; inspect {LOG_FILE}")
        if healthy():
            return True
        time.sleep(2)
    raise TimeoutError(f"ACE-Step did not become healthy within {timeout}s; inspect {LOG_FILE}")


def stop_server() -> bool:
    if not PID_FILE.is_file():
        return False
    pid = int(PID_FILE.read_text(encoding="utf-8").strip())
    try:
        command = subprocess.check_output(["ps", "-p", str(pid), "-o", "command="], text=True).strip()
    except subprocess.CalledProcessError:
        PID_FILE.unlink(missing_ok=True)
        return False
    if "acestep-api" not in command:
        raise RuntimeError(f"refusing to stop PID {pid}; command is not ACE-Step: {command}")
    os.killpg(pid, signal.SIGTERM)
    PID_FILE.unlink(missing_ok=True)
    return True


def generate(args: argparse.Namespace) -> Path:
    started_here = start_server(args.startup_timeout)
    try:
        body = {
            "prompt": args.prompt,
            "lyrics": args.lyrics,
            "thinking": args.thinking,
            "audio_duration": args.duration,
            "inference_steps": 8,
            "batch_size": 1,
            "use_random_seed": False,
            "seed": args.seed,
            "audio_format": "wav",
            "bpm": args.bpm,
            "use_cot_caption": args.thinking,
            "use_cot_language": args.thinking,
            "lm_model_path": "acestep-5Hz-lm-0.6B",
            "lm_backend": "mlx",
        }
        released = request_json("/release_task", body, timeout=60)
        task_id = str((released.get("data") or {}).get("task_id") or "")
        if not task_id:
            raise RuntimeError(f"ACE-Step did not return a task id: {released}")
        deadline = time.monotonic() + args.render_timeout
        result_item: dict[str, object] | None = None
        while time.monotonic() < deadline:
            queried = request_json("/query_result", {"task_id_list": [task_id]}, timeout=30)
            rows = queried.get("data") or []
            if rows:
                status = int(rows[0].get("status", 0))
                if status == 2:
                    raise RuntimeError(f"ACE-Step generation failed: {rows[0]}")
                if status == 1:
                    parsed = json.loads(rows[0].get("result") or "[]")
                    if not parsed:
                        raise RuntimeError("ACE-Step succeeded without an audio result")
                    result_item = parsed[0]
                    break
            time.sleep(3)
        if result_item is None:
            raise TimeoutError(f"ACE-Step render exceeded {args.render_timeout}s")
        file_url = str(result_item.get("file") or "")
        if not file_url:
            raise RuntimeError(f"ACE-Step result lacks an audio URL: {result_item}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(BASE_URL + file_url, timeout=120) as response:
            args.output.write_bytes(response.read())
        return args.output
    finally:
        if started_here and not args.keep_server:
            stop_server()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("preflight")
    sub.add_parser("status")
    start = sub.add_parser("start")
    start.add_argument("--startup-timeout", type=float, default=900)
    sub.add_parser("stop")
    render = sub.add_parser("generate")
    render.add_argument("--prompt", required=True)
    render.add_argument("--lyrics", default="[Instrumental]")
    render.add_argument("--duration", type=float, default=10)
    render.add_argument("--bpm", type=int, default=96)
    render.add_argument("--seed", type=int, default=20260713)
    render.add_argument("--thinking", action="store_true")
    render.add_argument("--output", type=Path, default=DEFAULT_OUTPUT / "ace-step-proof.wav")
    render.add_argument("--startup-timeout", type=float, default=900)
    render.add_argument("--render-timeout", type=float, default=1800)
    render.add_argument("--keep-server", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "preflight":
            status = preflight()
            print(json.dumps(status, indent=2))
            return 0 if status["ready"] else 1
        if args.command == "status":
            print(json.dumps(preflight(), indent=2))
            return 0
        if args.command == "start":
            print(json.dumps({"started": start_server(args.startup_timeout), "health": healthy(), "log": str(LOG_FILE)}, indent=2))
            return 0
        if args.command == "stop":
            print(json.dumps({"stopped": stop_server()}, indent=2))
            return 0
        print(generate(args))
        return 0
    except (OSError, RuntimeError, TimeoutError, ValueError, urllib.error.URLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
