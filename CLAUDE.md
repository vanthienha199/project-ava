# Project Ava — Claude Code Instructions

## FIRST: Read These Files
1. `/Users/hale/projects/project-ava/PROGRESS.md` — Full context, architecture, environment, tasks
2. `/Users/hale/projects/project-ava/research/RESEARCH_FINDINGS.md` — cocotb 2.0 traps, CorrectBench algorithm, prompt rules

## What This Is
AI agent that generates cocotb (Python) verification testbenches for Verilog designs, runs Icarus Verilog simulation, and self-corrects until tests pass.

## Environment
- **Venv:** `source /Users/hale/projects/project-ava/venv/bin/activate` (Python 3.13 — cocotb 2.0 needs ≤3.13)
- **Simulator:** `iverilog` + `vvp` (Icarus Verilog 13.0)
- **LLM primary:** `echo "prompt" | claude -p` (Max plan, free)
- **LLM backup:** Ollama at localhost:11434, model deepseek-coder:6.7b
- **Run cocotb tests:** `cd <design_dir> && make SIM=icarus`

## CRITICAL: cocotb 2.0 API Rules
Every LLM prompt that generates cocotb code MUST include these rules:
1. Use `int(dut.signal.value)` to read values, NEVER `.value.integer`
2. Single-bit signals return `Logic` type, use `int()` to convert
3. Use `Timer(N, unit="ns")`, NOT `units="ns"`
4. Use `cocotb.start_soon()`, NOT `cocotb.fork()`
5. Use `task.cancel()`, NOT `task.kill()`
6. Use `assert` for failures, NOT `raise TestFailure()`
7. No arithmetic on `LogicArray` — convert to `int()` first
8. Do NOT import `BinaryValue` — use `LogicArray` if needed
9. Do NOT use `.value.binstr` — use `str(value)` instead
10. Slice assignments must match exact width

## Git Rules
- Author: `--author="Ha Le <halevanthien@gmail.com>"`
- NEVER add Co-Authored-By Claude. NEVER mention Claude in commits.
- Repo: github.com/vanthienha199/project-ava
