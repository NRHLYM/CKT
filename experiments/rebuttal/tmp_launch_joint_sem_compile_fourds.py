#!/usr/bin/env python3
"""Four-dataset joint semantic+compile critiques then merged repair.

Skips a dataset via JOINT_SKIP (comma-separated). Does not kill the live CVDP job.
"""
from __future__ import annotations

from pathlib import Path as _CktPath
import os as _ckt_os
CKT_WORK = _CktPath(_ckt_os.environ.get('CKT_WORK', str(_CktPath.home() / 'ckt_work')))
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT = CKT_WORK / "ckt_joint_sem_compile_20260921"
PRIVATE = CKT_WORK / "nl2chip_joint_sem_compile_private_20260921"
NL2CHIP = CKT_WORK / "Ckt"
PYTHON = CKT_WORK / "Ckt/.venv/bin/python"
OUT = CKT_WORK / "ckt_artifacts/2026-09-21/sparkle_joint_sem_compile_fourds"
ARCHON_SRC = CKT_WORK / "archon-official/src"
WRAPPER = PRIVATE / "codex_chatgpt_socks.py"
DUMMY_KEY = CKT_WORK / "nl2chip_chatgpt_socks_private_20260918/dummy.key.env"
CVDP168 = CKT_WORK / "cvdp_mainline_168_problem_ids.txt"
SOCKS_SRC = CKT_WORK / "nl2chip_chatgpt_socks_private_20260918/codex_chatgpt_socks.py"
WORKERS = int(os.environ.get("JOINT_WORKERS", "2"))

JOBS = (
    ("verilogeval", "legacy", 156, None),
    ("rtllm", "legacy", 50, None),
    ("resbench", "legacy", 56, None),
    ("cvdp", "public-spec-v2", 168, CVDP168),
)


def environment() -> dict[str, str]:
    env = os.environ.copy()
    env["NL2CHIP_ISOLATION_ROOT"] = str(PRIVATE / "agent_state")
    env["PYTHONPATH"] = str(PROJECT) + ":" + str(PROJECT / "agent")
    env["PATH"] = (
        str(_CktPath.home() / ".local/bin:${HOME}/.elan/toolchains/")
        "leanprover--lean4---v4.28.0-rc1/bin:" + env.get("PATH", "")
    )
    env["CVDP_HARNESS_PROFILE"] = "race-safe-v1"
    env["CVDP_DATASET_FILE"] = str(
        Path(str(CKT_WORK / "benchmarks/cvdp-benchmark-dataset/")
             "cvdp_v1.1.0_nonagentic_code_generation_no_commercial.jsonl")
    )
    for name in (
        "LLM_API_KEY", "LLM_BASE_URL", "CODEX_GATEWAY_API_KEY",
        "OPENAI_API_KEY", "OPENAI_BASE_URL",
    ):
        env.pop(name, None)
    return env


def prepare_private() -> None:
    PRIVATE.mkdir(parents=True, exist_ok=True)
    os.chmod(PRIVATE, 0o700)
    (PRIVATE / "agent_state").mkdir(exist_ok=True)
    if WRAPPER.exists():
        return
    text = SOCKS_SRC.read_text()
    text = text.replace(
        'ROOT = CKT_WORK / "eval_sparkle_tree"',
        f'ROOT = Path("{PROJECT}")',
    )
    text = text.replace(
        'ISOLATION_PARENT = CKT_WORK / "nl2chip_chatgpt_socks_private_20260918/agent_state"',
        f'ISOLATION_PARENT = Path("{PRIVATE / "agent_state"}")',
    )
    WRAPPER.write_text(text)
    os.chmod(WRAPPER, 0o700)


def symlink_datasets() -> None:
    for name in ("verilog-eval", "RTLLM", "ResBench"):
        dest = PROJECT / name
        src = NL2CHIP / name
        if dest.exists() or dest.is_symlink():
            continue
        if src.exists():
            dest.symlink_to(src)


def command(dataset: str, policy: str, results_dir: Path, problem_file: Path | None) -> list[str]:
    cmd = [
        str(PYTHON), "-u", "-m", "cktarchon.run",
        "--dataset", dataset,
        "--results-dir", str(results_dir),
        "--workers", str(WORKERS),
        "--resume", "--resume-mode", "completed",
        "--interface-prompt-policy", policy,
        "--cvdp-harness-profile", "race-safe-v1",
        "--model", "gpt-5.6-sol",
        "--max-tokens", "16384",
        "--harness", "codex-agent",
        "--max-turns", "40",
        "--total-turn-budget", "100",
        "--generation-turn-cap", "40",
        "--prompt-profile", "compact",
        "--archon-src", str(ARCHON_SRC),
        "--codex-bin", str(WRAPPER),
        "--codex-effort", "ultra",
        "--codex-sandbox", "workspace-write",
        "--no-codex-chat-proxy",
        "--hide-cvdp-harness-from-agent",
        "--key-env", str(DUMMY_KEY),
        "--sim-feedback",
        "--feedback-mode", "compile-only",
        "--joint-semantic-compile-feedback",
        "--sim-feedback-max-iters", "9",
        "--sim-feedback-turns-per-iter", "10",
        "--sim-feedback-patience", "0",
    ]
    if problem_file is not None:
        cmd.extend(["--problem-file", str(problem_file)])
    return cmd


def main() -> int:
    if "--joint-semantic-compile-feedback" not in (PROJECT / "cktarchon" / "run.py").read_text():
        raise SystemExit("run.py missing joint flag")
    skip = {x.strip() for x in os.environ.get("JOINT_SKIP", "").split(",") if x.strip()}
    only = os.environ.get("JOINT_ONLY")
    subprocess.check_call(["bash", str(CKT_WORK / "codex_auth/ensure_socks.sh")])
    prepare_private()
    symlink_datasets()
    OUT.mkdir(parents=True, exist_ok=True)
    stamp = os.environ.get("FOURDS_STAMP") or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    env = environment()
    launched = []
    rc = 0
    for dataset, policy, expected, problem_file in JOBS:
        if only and dataset != only:
            continue
        if dataset in skip:
            print(json.dumps({"phase": "skip", "dataset": dataset}), flush=True)
            continue
        subprocess.check_call(["bash", str(CKT_WORK / "codex_auth/ensure_socks.sh")])
        results = OUT / f"{dataset}_{stamp}"
        results.mkdir(parents=True, exist_ok=True)
        cmd = command(dataset, policy, results, problem_file)
        entry = {"dataset": dataset, "expected": expected, "workers": WORKERS, "results": str(results)}
        print(json.dumps({"phase": "start", **entry}), flush=True)
        with (results / "launcher.log").open("ab") as log:
            code = subprocess.call(
                cmd, cwd=str(PROJECT), env=env,
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
            )
        entry["exit_code"] = code
        launched.append(entry)
        (OUT / "launch.json").write_text(json.dumps({
            "protocol": "joint-semantic-compile-critiques",
            "model": "gpt-5.6-sol",
            "jobs": launched,
        }, indent=2) + "\n")
        if code != 0:
            rc = code
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
