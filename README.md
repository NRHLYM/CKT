# CKT

Anonymous artifact for **natural-language → synthesizable hardware** using Lean 4 and an agent harness.

This tree is a cleaned snapshot of the evaluation code. It does not include datasets, run artifacts, API keys, or author identities.

## Layout

| Path | Role |
|---|---|
| `Sparkle/` | Lean hardware DSL, compiler, Verilog backend |
| `cktarchon/` | Generation harness (tools, Lean check, compile/sim loop) |
| `agent/` | Benchmark adapters and evaluators |
| `experiments/` | Launch scripts (VerilogEval / RTLLM / CVDP / PPA / contracts) |
| `Tests/` | Lean and Python tests |
| `docs/` | Language and harness notes |

## Setup

```bash
export CKT_WORK="$HOME/ckt_work"          # local work/output root
export CKT_PROJECT="$PWD"                 # this repo
python3 -m venv .venv && . .venv/bin/activate
pip install -e .
# Lean 4: install elan, then `lake build` from the repo root
```

LLM credentials belong in a **chmod 600** env file that is **not** committed:

```bash
cp .env.example llm.env
# fill OPENAI_API_KEY / OPENAI_BASE_URL (any OpenAI-compatible chat endpoint)
export LLM_ENV="$PWD/llm.env"
```

Point dataset roots at **your** copies of VerilogEval / RTLLM / CVDP. They are not vendored here.

## Formal contracts (NL → observational Lean)

```
experiments/rebuttal/tmp_contract_validate.py
experiments/rebuttal/tmp_contract_checkers.py
experiments/rebuttal/tmp_launch_contract_*.py
```

Set `LAKE_DIR` to this repo (or a Lean HDL checkout that `lake env lean` can use). Checker hard gates are syntax ∧ soundness ∧ completeness; completeness only scores mutants whose I/O traces **diverge** from the reference.

## What was stripped

- Host-specific home directories and cluster names
- Vendor LLM hostnames and secrets
- Benchmark dumps, `Generated/`, waveforms, and result jsonl trees
- Git history from the internal repository

## License

Apache-2.0. See `LICENSE`.
